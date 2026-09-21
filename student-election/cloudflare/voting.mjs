const q=(e,s,...a)=>e.DB.prepare(s).bind(...a);
const fail=(error,status=400)=>{throw Object.assign(new Error(error),{status})};
const digest=async text=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))),b=>b.toString(16).padStart(2,'0')).join('');
async function credential(env,email,code){
 if(!env.CREDENTIAL_KEY)fail('unavailable',503);
 const k=await crypto.subtle.importKey('raw',new TextEncoder().encode(env.CREDENTIAL_KEY),{name:'HMAC',hash:'SHA-256'},false,['sign']);
 return Array.from(new Uint8Array(await crypto.subtle.sign('HMAC',k,new TextEncoder().encode(email+'\0'+code))),b=>b.toString(16).padStart(2,'0')).join('');
}
export async function votingGet(env,config,origin){
 const s=await q(env,'SELECT ballot_config FROM settings WHERE id=1').first();
 if(s.ballot_config)return JSON.parse(s.ballot_config);
 const {results}=await q(env,'SELECT id,office,profile,revision FROM candidates WHERE approved_revision=revision AND public_photo IS NOT NULL').all();
 return {...config,mode:'draft',offices:config.offices.map(o=>({...o,candidates:results.filter(c=>c.office===o.id).map(c=>({id:c.id,revision:c.revision,...JSON.parse(c.profile),photo:origin+'/photos/'+c.id}))}))};
}
export async function votingPost(path,b,env,config,origin){
 const s=await q(env,'SELECT ballot_config FROM settings WHERE id=1').first(),ballot=s.ballot_config?JSON.parse(s.ballot_config):null;
 if(path==='/admin/voting/schedule'){
  if(ballot)fail('already_scheduled',409);
  const start=Date.parse(b.opensAt),end=Date.parse(b.closesAt);
  if(!Number.isFinite(start)||!Number.isFinite(end)||start<=Date.now()||end<=start||!/[Zz]|[+-]\d\d:\d\d$/.test(b.opensAt)||!/[Zz]|[+-]\d\d:\d\d$/.test(b.closesAt))fail('invalid_dates');
  const current=await votingGet(env,config,origin);
  if(current.offices.some(o=>!o.candidates.length))fail('missing_candidates');
  // Guard against approvals changing between reading and freezing.
  const ids=current.offices.flatMap(o=>o.candidates.map(c=>c.id+':'+c.revision)).sort().join(',');
  const result=await q(env,"UPDATE settings SET ballot_config=?,profiles_open=0,nominations_open=0 WHERE id=1 AND ballot_config IS NULL AND (SELECT group_concat(signature,',') FROM (SELECT id||':'||revision AS signature FROM candidates WHERE approved_revision=revision AND public_photo IS NOT NULL ORDER BY id))=?",JSON.stringify({...current,mode:'live',opensAt:new Date(start).toISOString(),closesAt:new Date(end).toISOString()}),ids).run();
  if(!result.meta.changes)fail('review_changed',409);
  return {ok:true};
 }
 if(path==='/admin/voting/register'){
  if(ballot&&Date.now()>=Date.parse(ballot.opensAt))fail('closed',409);
  if(typeof b.email!=='string'||! /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(b.email)||b.email.length>254||typeof b.code!=='string'||!/^[A-Z2-9]{3}$/.test(b.code))fail('invalid_credentials');
  const email=b.email.trim().toLowerCase(),id=await digest(email),h=await credential(env,email,b.code);
  await q(env,'INSERT OR IGNORE INTO voters(identity_hash,token_hash) VALUES(?,?)',id,h).run();
  const row=await q(env,'SELECT token_hash FROM voters WHERE identity_hash=?',id).first();
  if(row.token_hash!==h)fail('already_issued',409);
  return {ok:true};
 }
 if(path==='/admin/voting/unlock'){
  if(typeof b.email!=='string')fail('invalid_request');
  await q(env,'UPDATE voters SET failures=0 WHERE identity_hash=?',await digest(b.email.trim().toLowerCase())).run();return {ok:true};
 }
 if(path==='/admin/voting/results'){
  if(!ballot||Date.now()<Date.parse(ballot.closesAt))fail('closed',409);
  const counts=Object.fromEntries(ballot.offices.map(o=>[o.id,Object.fromEntries([...o.candidates.map(c=>[c.id,0]),['ABSTAIN',0]])]));
  const {results}=await q(env,'SELECT choices FROM ballots').all();
  for(const r of results)for(const [o,c] of Object.entries(JSON.parse(r.choices)))counts[o][c]++;
  return {electionId:config.electionId,eligible:(await q(env,'SELECT count(*) n FROM voters').first()).n,ballots:results.length,counts,note:'Counts only; apply chapter rules to certify winners and resolve ties.'};
 }
 if(path!=='/ballots')fail('not_found',404);
 if(b.electionId!==config.electionId)fail('invalid_ballot');
 if(typeof b.email!=='string'||typeof b.token!=='string'||b.email.length>254||b.token.trim().length!==3)fail('invalid_credentials',403);
 const email=b.email.trim().toLowerCase(),id=await digest(email),h=await credential(env,email,b.token.trim().toUpperCase());
 const voter=await q(env,'SELECT * FROM voters WHERE identity_hash=?',id).first();
 if(!voter||voter.failures>=5)fail('invalid_credentials',403);
 if(voter.token_hash!==h){await q(env,'UPDATE voters SET failures=failures+1 WHERE identity_hash=?',id).run();fail('invalid_credentials',403)}
 if(voter.receipt)return {receipt:voter.receipt,alreadyRecorded:true};
 if(!ballot||Date.now()<Date.parse(ballot.opensAt)||Date.now()>=Date.parse(ballot.closesAt))fail('closed',409);
 if(!b.choices||typeof b.choices!=='object'||Object.keys(b.choices).sort().join(',')!==ballot.offices.map(o=>o.id).sort().join(',')||ballot.offices.some(o=>![...o.candidates.map(c=>c.id),'ABSTAIN'].includes(b.choices[o.id])))fail('invalid_ballot');
 const receipt=crypto.randomUUID();
 await q(env,'INSERT INTO claims(identity_hash,receipt,choices,ballot_id) SELECT identity_hash,?,?,? FROM voters WHERE identity_hash=? AND token_hash=? AND receipt IS NULL AND failures<5',receipt,JSON.stringify(b.choices),crypto.randomUUID(),id,h).run();
 const saved=await q(env,'SELECT receipt FROM voters WHERE identity_hash=?',id).first();
 if(!saved.receipt)fail('invalid_credentials',403);
 return {receipt:saved.receipt,alreadyRecorded:saved.receipt!==receipt};
}
