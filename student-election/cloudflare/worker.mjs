import config from '../config.json';
import {votingGet,votingPost} from './voting.mjs';
const offices=config.offices.map(({id,th,en,type})=>({id,th,en,type,candidates:[]}));
const encode=new TextEncoder();
export async function hash(value){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',encode.encode(value))),b=>b.toString(16).padStart(2,'0')).join('')}
const now=()=>Math.floor(Date.now()/1000);
const str=(x,max)=>typeof x==='string'&&x.trim().length>0&&x.trim().length<=max;
const email=x=>str(x,254)&&/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(x);
const office=x=>offices.some(o=>o.id===x);
const query=(env,sql,...args)=>env.DB.prepare(sql).bind(...args);
function fail(error,status=400){throw Object.assign(new Error(error),{status})}
function imageBytes(photo){
 if(typeof photo!=='string'||photo.length>7000000)fail('invalid_photo');
 let bytes;try{bytes=Uint8Array.from(atob(photo),c=>c.charCodeAt(0))}catch{fail('invalid_photo')}
 if(bytes.length>5242880||bytes.length<12)fail('invalid_photo');
 const jpeg=bytes[0]===255&&bytes[1]===216&&bytes[2]===255;
 const png=[137,80,78,71,13,10,26,10].every((b,i)=>bytes[i]===b);
 if(!jpeg&&!png)fail('invalid_photo');return {bytes,type:jpeg?'image/jpeg':'image/png'};
}
export default {async fetch(request,env){
 const url=new URL(request.url),path=url.pathname,method=request.method;
 const headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Vary':'Origin'};
 if(request.headers.get('Origin')===env.ORIGIN)headers['Access-Control-Allow-Origin']=env.ORIGIN;
 const reply=(data,status=200)=>Response.json(data,{status,headers});
 try{
  if(method==='GET'&&path==='/election')return reply(await votingGet(env,config,url.origin));
  if(method==='GET'&&path==='/health'){await query(env,'SELECT id FROM settings WHERE id=1').first();return reply({status:'ok'})}
  if(method==='GET'&&path==='/intake'){const s=await query(env,'SELECT * FROM settings WHERE id=1').first();return reply({nominationsOpen:!!s.nominations_open})}
  if(method==='GET'&&path==='/approved'){
   const {results}=await query(env,'SELECT id,office,profile,revision FROM candidates WHERE approved_revision=revision AND public_photo IS NOT NULL').all();
   return reply({electionId:config.electionId,title:'Chulalongkorn University Student Chapter Election',offices:offices.map(o=>({...o,title:o.en,candidates:results.filter(c=>c.office===o.id).map(c=>({id:c.id,...JSON.parse(c.profile),photo:url.origin+'/photos/'+c.id}))}))});
  }
  if(method==='GET'&&/^\/photos\/[a-f0-9-]{36}$/.test(path)){
   const row=await query(env,'SELECT public_photo FROM candidates WHERE id=? AND approved_revision=revision',path.split('/')[2]).first();
   if(!row?.public_photo)fail('not_found',404);const object=await env.PHOTOS.get(row.public_photo);if(!object)fail('not_found',404);
   return new Response(object.body,{headers:{...headers,'Content-Type':'image/jpeg','Content-Security-Policy':"default-src 'none'"}});
  }
  const admin=path.startsWith('/admin/');
  if(admin){
   const secret=request.headers.get('Authorization')?.replace(/^Bearer /,'')||'';
   if(!env.ADMIN_TOKEN||!secret||await hash(secret)!==await hash(env.ADMIN_TOKEN))fail('unauthorized',403);
  }else{
   if(!['/ballots','/nominations','/candidate/profile','/candidate/submit'].includes(path))fail('not_found',404);
   if(request.headers.get('Origin')!==env.ORIGIN)fail('origin',403);
  }
  if(method==='OPTIONS')return new Response(null,{status:204,headers:{...headers,'Access-Control-Allow-Methods':'POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type'}});
  if(method!=='POST')fail('method',405);
  // CF-Connecting-IP is supplied by Cloudflare, not an arbitrary forwarding chain.
  const window=Math.floor(now()/60),key=await hash(request.headers.get('CF-Connecting-IP')||'local');
  const limit=await query(env,'INSERT INTO request_limits(key,window,count) VALUES(?,?,1) ON CONFLICT(key) DO UPDATE SET count=CASE WHEN window=excluded.window THEN count+1 ELSE 1 END,window=excluded.window RETURNING count',key,window).first();
  if(limit.count>30)fail('rate_limited',429);
  await query(env,'DELETE FROM request_limits WHERE window<?',window-2).run();
  if(!(request.headers.get('Content-Type')||'').startsWith('application/json'))fail('invalid_request');
  const max=path.endsWith('/submit')||path.endsWith('/sanitize')?7100000:16384;
  const reader=request.body?.getReader();if(!reader)fail('invalid_request');let size=0,chunks=[];
  while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>max){await reader.cancel();fail('invalid_request',413)}chunks.push(value)}
  const raw=new Uint8Array(size);let offset=0;for(const part of chunks){raw.set(part,offset);offset+=part.length}let b;try{b=JSON.parse(new TextDecoder().decode(raw))}catch{fail('invalid_request')}
  if(!b||typeof b!=='object'||Array.isArray(b))fail('invalid_request');
  const settings=await query(env,'SELECT * FROM settings WHERE id=1').first();
  if(path==='/ballots'||path.startsWith('/admin/voting/'))return reply(await votingPost(path,b,env,config,url.origin));
  if(admin){
   if(path==='/admin/intake'){if(settings.ballot_config)fail('frozen',409);if(typeof b.open!=='boolean')fail('invalid_request');await query(env,'UPDATE settings SET nominations_open=? WHERE id=1',+b.open).run();return reply({ok:true})}
   if(path==='/admin/list'){return reply({nominations:(await query(env,'SELECT * FROM nominations ORDER BY created').all()).results,candidates:(await query(env,'SELECT id,office,profile,revision,shortlisted_revision,approved_revision,consent_at FROM candidates').all()).results})}
   if(path==='/admin/invite'){
    if(!str(b.name,150))fail('invalid_profile');const id=crypto.randomUUID(),token=Array.from(crypto.getRandomValues(new Uint8Array(32)),v=>v.toString(16).padStart(2,'0')).join('');
    await query(env,'INSERT INTO candidates(id,invite_hash,expires,profile) VALUES(?,?,?,?)',id,await hash(token),now()+14*86400,JSON.stringify({name:b.name.trim(),affiliation:'',bio:''})).run();
    return reply({id,upload_link:'https://ecs-thai.github.io/student-election/candidate.html#invite='+token});
   }
   if(settings.ballot_config)fail('frozen',409);
   const c=await query(env,'SELECT * FROM candidates WHERE id=?',typeof b.id==='string'?b.id:'').first();if(!c)fail('not_found',404);
   if(path==='/admin/photo'){const p=await env.PHOTOS.get(c.photo_key);if(!p)fail('not_found',404);return new Response(p.body,{headers:{...headers,'Content-Type':'application/octet-stream'}})}
   if(!Number.isInteger(b.revision)||b.revision!==c.revision)fail('revision_changed',409);
   if(path==='/admin/sanitize'){
    const {bytes,type}=imageBytes(b.photo);if(type!=='image/jpeg')fail('invalid_photo');const key='sanitized/'+c.id+'/'+c.revision+'/'+crypto.randomUUID()+'.jpg';await env.PHOTOS.put(key,bytes,{httpMetadata:{contentType:'image/jpeg'}});
    const r=await query(env,'UPDATE candidates SET public_photo=? WHERE id=? AND revision=?',key,c.id,c.revision).run();if(!r.meta.changes)fail('revision_changed',409);return reply({ok:true});
   }
   if(path==='/admin/shortlist'||path==='/admin/approve'){
    if(!c.consent_at||!c.photo_key||!c.office||!c.public_photo)fail('incomplete');
    const isApprove=path.endsWith('/approve');
    const action=isApprove?'approved':'shortlisted',column=isApprove?'approved_revision':'shortlisted_revision';
    const r=await query(env,`UPDATE candidates SET ${column}=revision WHERE id=? AND revision=?`,c.id,c.revision).run();if(!r.meta.changes)fail('revision_changed',409);
    await query(env,'INSERT INTO audit(candidate_id,action,revision,created) VALUES(?,?,?,?)',c.id,action,c.revision,now()).run();return reply({ok:true});
   }
   fail('not_found',404);
  }
  if(path==='/nominations'){
   if(!settings.nominations_open)fail('closed',409);
   if(!str(b.name,150)||!email(b.email)||!office(b.office)||!['self','nominate'].includes(b.kind)||b.contactConsent!==true)fail('invalid_request');
   if(b.kind==='nominate'&&(!str(b.nominatorName,150)||!email(b.nominatorEmail)))fail('invalid_request');
   const data={name:b.name.trim(),email:b.email.trim().toLowerCase(),office:b.office,kind:b.kind,nominatorName:b.kind==='self'?b.name.trim():b.nominatorName.trim(),nominatorEmail:(b.kind==='self'?b.email:b.nominatorEmail).trim().toLowerCase()};
   await query(env,'INSERT OR IGNORE INTO nominations VALUES(?,?,?,?,?)',crypto.randomUUID(),data.email,data.office,JSON.stringify(data),now()).run();return reply({status:'received'});
  }
  if(!str(b.invite,100)||b.invite.length<30)fail('invalid_invite',403);
  const c=await query(env,'SELECT * FROM candidates WHERE invite_hash=?',await hash(b.invite)).first();if(!c||c.expires<now())fail('invalid_invite',403);
  if(path==='/candidate/profile')return reply({profile:JSON.parse(c.profile),office:offices.find(o=>o.id===c.office)||null,offices,hasPhoto:!!c.photo_key,submitted:!!c.consent_at,approved:c.approved_revision===c.revision,locked:!settings.profiles_open});
  if(!settings.profiles_open)fail('closed',409);
  if(!office(b.office))fail('invalid_office');
  if(!str(b.name,150)||!str(b.affiliation,200)||!str(b.bio,3000)||b.consent!==true)fail('invalid_profile');
  let photo=c.photo_key;
  if(b.photo){const {bytes,type}=imageBytes(b.photo);photo='private/'+c.id+'/'+crypto.randomUUID();await env.PHOTOS.put(photo,bytes,{httpMetadata:{contentType:type}})}
  if(!photo)fail('invalid_photo');
  const profile={name:b.name.trim(),affiliation:b.affiliation.trim(),bio:b.bio.trim()};
  const result=await query(env,'UPDATE candidates SET profile=?,office=?,photo_key=?,public_photo=NULL,revision=revision+1,shortlisted_revision=NULL,approved_revision=NULL,consent_at=? WHERE id=? AND revision=?',JSON.stringify(profile),b.office,photo,now(),c.id,c.revision).run();
  if(!result.meta.changes)fail('revision_changed',409);return reply({status:'pending_review'});
 }catch(error){return reply({error:error.status?error.message:'service_unavailable'},error.status||503)}
}};
