const q=(e,s,...a)=>e.DB.prepare(s).bind(...a);
const now=()=>Math.floor(Date.now()/1000);
const fail=(error,status=400)=>{throw Object.assign(new Error(error),{status})};
const hash=async s=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s))),b=>b.toString(16).padStart(2,'0')).join('');
const text=(s,n)=>typeof s==='string'&&s.trim().length>0&&s.trim().length<=n;
const email=s=>text(s,254)&&/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);
function publicPost(r){return {id:r.id,kind:r.kind,...JSON.parse(r.body),updated:r.updated}}
function validate(b){
 if(!['opportunity','lab','event'].includes(b.kind))fail('invalid_kind');
 const p={};
 for(const [key,max] of Object.entries({title:180,institution:200,location:150,tags:300,description:6000,contact:254,link:2000,funding:300,category:40,start:40,end:40,deadline:40})){
  if(b[key]!==undefined&&typeof b[key]!=='string')fail('invalid_fields');p[key]=(b[key]||'').trim();if(p[key].length>max)fail('invalid_fields');
 }
 if(!p.title||!p.institution||!p.description||!email(p.contact)||b.consent!==true)fail('invalid_fields');
 if(p.link){let u;try{u=new URL(p.link)}catch{fail('invalid_link')}if(!['https:','http:'].includes(u.protocol)||u.username||u.password)fail('invalid_link')}
 if(b.kind==='opportunity'&&!['intern','assistant','masters','phd','postdoc','job'].includes(p.category))fail('invalid_category');
 if(b.kind==='opportunity'&&(!/^\d{4}-\d{2}-\d{2}$/.test(p.deadline)||!Number.isFinite(Date.parse(p.deadline))||Date.parse(p.deadline+'T23:59:59+07:00')<Date.now()))fail('invalid_dates');
 if(b.kind==='event'&&(!Number.isFinite(Date.parse(p.start))||!Number.isFinite(Date.parse(p.end))||Date.parse(p.start)>=Date.parse(p.end)||Date.parse(p.end)<Date.now()||!/(Z|[+-]\d\d:\d\d)$/.test(p.start)||!/(Z|[+-]\d\d:\d\d)$/.test(p.end)))fail('invalid_dates');
 return p;
}
function expired(p){return p.kind==='event'?Date.parse(p.end)<Date.now():p.kind==='opportunity'?Date.parse(p.deadline+'T23:59:59+07:00')<Date.now():false}
export default {async fetch(req,env){
 const path=new URL(req.url).pathname;
 const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Vary':'Origin'};
 if(req.headers.get('Origin')===env.ORIGIN)headers['Access-Control-Allow-Origin']=env.ORIGIN;
 const reply=(data,status=200)=>Response.json(data,{status,headers});
 try{
  if(req.method==='GET'&&path==='/health'){await q(env,'SELECT count(*) FROM posts').first();return reply({status:'ok'})}
  if(req.method==='GET'&&path==='/posts'){
   const rows=(await q(env,"SELECT * FROM posts WHERE status IN ('approved','closed') ORDER BY updated DESC LIMIT 500").all()).results;
   return reply({posts:rows.map(r=>{const p=publicPost(r);return {...p,archived:r.status==='closed'||expired(p)}})});
  }
  if(req.headers.get('Origin')&&req.headers.get('Origin')!==env.ORIGIN)fail('origin',403);
  if(req.method==='OPTIONS')return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'POST, GET, OPTIONS','Access-Control-Allow-Headers':'Content-Type, Authorization'}});
  if(req.method!=='POST')fail('not_found',404);
  const key=await hash(req.headers.get('CF-Connecting-IP')||'local'),window=Math.floor(now()/60);
  const limit=await q(env,'INSERT INTO limits VALUES(?,?,1) ON CONFLICT(key) DO UPDATE SET count=CASE WHEN window=excluded.window THEN count+1 ELSE 1 END,window=excluded.window RETURNING count',key,window).first();
  if(limit.count>40)fail('rate_limited',429);await q(env,'DELETE FROM limits WHERE window<?',window-2).run();
  if(!req.headers.get('Content-Type')?.startsWith('application/json'))fail('invalid_request');
  const reader=req.body?.getReader();if(!reader)fail('invalid_request');let size=0,parts=[];
  while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>32768){await reader.cancel();fail('too_large',413)}parts.push(value)}
  const raw=new Uint8Array(size);let offset=0;for(const p of parts){raw.set(p,offset);offset+=p.length}let b;try{b=JSON.parse(new TextDecoder().decode(raw))}catch{fail('invalid_request')}
  if(!b||typeof b!=='object'||Array.isArray(b))fail('invalid_request');
  if(path==='/access'){
   if(!text(b.name,150)||!email(b.email)||b.consent!==true)fail('invalid_fields');
   await q(env,'INSERT OR IGNORE INTO access_requests VALUES(?,?,?)',b.email.trim().toLowerCase(),b.name.trim(),now()).run();return reply({ok:true});
  }
  if(path==='/report'){
   if(!text(b.reason,1000)||!text(b.id,40))fail('invalid_fields');
   const post=await q(env,"SELECT id FROM posts WHERE id=? AND status IN ('approved','closed')",b.id).first();if(!post)fail('not_found',404);
   await q(env,'INSERT INTO reports(id,post_id,reason,created) VALUES(?,?,?,?)',crypto.randomUUID(),b.id,b.reason.trim(),now()).run();return reply({ok:true});
  }
  const token=req.headers.get('Authorization')?.replace(/^Bearer /,'')||'';
  const admin=!!env.ADMIN_TOKEN&&!!token&&await hash(token)===await hash(env.ADMIN_TOKEN);
  if(path.startsWith('/admin/')){
   if(!admin)fail('unauthorized',403);
   if(path==='/admin/list')return reply({posts:(await q(env,'SELECT p.*,m.name AS owner_name FROM posts p JOIN members m ON m.id=p.owner ORDER BY updated DESC LIMIT 500').all()).results,requests:(await q(env,'SELECT * FROM access_requests').all()).results,reports:(await q(env,'SELECT * FROM reports WHERE resolved=0').all()).results,members:(await q(env,'SELECT id,name,email,expires,active FROM members').all()).results});
   if(path==='/admin/invite'){
    if(!text(b.name,150)||!email(b.email))fail('invalid_fields');
    const token=Array.from(crypto.getRandomValues(new Uint8Array(32)),x=>x.toString(16).padStart(2,'0')).join(''),id=crypto.randomUUID(),e=b.email.trim().toLowerCase();
    await q(env,'INSERT INTO members(id,name,email,token_hash,expires) VALUES(?,?,?,?,?) ON CONFLICT(email) DO UPDATE SET name=excluded.name,token_hash=excluded.token_hash,expires=excluded.expires,active=1',id,b.name.trim(),e,await hash(token),now()+30*86400).run();
    await q(env,'DELETE FROM access_requests WHERE email=?',e).run();return reply({link:env.SITE+'/index.html#access='+token,expiresInDays:30});
   }
   if(path==='/admin/revoke'){await q(env,'UPDATE members SET active=0 WHERE id=?',b.id||'').run();return reply({ok:true})}
   if(path==='/admin/resolve'){await q(env,'UPDATE reports SET resolved=1 WHERE id=?',b.id||'').run();return reply({ok:true})}
   if(path==='/admin/review'){
    if(!['approved','rejected','hidden'].includes(b.status)||!Number.isInteger(b.revision))fail('invalid_fields');
    const r=await q(env,'UPDATE posts SET status=?,reason=?,updated=? WHERE id=? AND revision=?',b.status,String(b.reason||'').slice(0,1000),now(),b.id||'',b.revision).run();if(!r.meta.changes)fail('revision_changed',409);
    await q(env,'INSERT INTO audit(action,post_id,created) VALUES(?,?,?)',b.status,b.id,now()).run();return reply({ok:true});
   }
   fail('not_found',404);
  }
  if(!token)fail('unauthorized',403);
  const member=await q(env,'SELECT * FROM members WHERE token_hash=? AND active=1 AND expires>?',await hash(token),now()).first();if(!member)fail('unauthorized',403);
  if(path==='/mine')return reply({name:member.name,posts:(await q(env,'SELECT * FROM posts WHERE owner=? ORDER BY updated DESC',member.id).all()).results});
  if(path==='/save'){
   const body=validate(b),id=b.id||crypto.randomUUID();
   if(b.id){
    if(!Number.isInteger(b.revision))fail('invalid_fields');
    const r=await q(env,"UPDATE posts SET kind=?,body=?,status='pending',reason='',revision=revision+1,updated=? WHERE id=? AND owner=? AND revision=?",b.kind,JSON.stringify(body),now(),id,member.id,b.revision).run();if(!r.meta.changes)fail('revision_changed',409);
   }else await q(env,'INSERT INTO posts(id,owner,kind,body,created,updated) VALUES(?,?,?,?,?,?)',id,member.id,b.kind,JSON.stringify(body),now(),now()).run();
   return reply({id,status:'pending'});
  }
  if(path==='/close'){
   await q(env,"UPDATE posts SET status=CASE WHEN status='approved' THEN 'closed' ELSE 'withdrawn' END,revision=revision+1,updated=? WHERE id=? AND owner=?",now(),b.id||'',member.id).run();return reply({ok:true});
  }
  fail('not_found',404);
 }catch(e){return reply({error:e.status?e.message:'service_unavailable'},e.status||503)}
}};
