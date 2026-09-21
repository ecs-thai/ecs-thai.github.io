"""Synthetic localhost-only integration checks; never issue or email real codes."""
import base64,io,json,time,urllib.request,urllib.error,uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone,timedelta
from PIL import Image
API='http://127.0.0.1:8791'
def call(route,body=None,admin=False,expected=200):
 headers={'Content-Type':'application/json','Origin':'https://ecs-thai.github.io'}
 if admin:headers['Authorization']='Bearer local-student-test-admin'
 for attempt in range(2):
  req=urllib.request.Request(API+route,data=json.dumps(body).encode() if body is not None else None,headers=headers)
  try:r=urllib.request.urlopen(req)
  except urllib.error.HTTPError as e:r=e
  if r.status==429 and attempt==0:time.sleep(61-time.time()%60);continue
  raw=r.read()
  assert r.status==expected,(route,r.status,raw[:200])
  return json.loads(raw) if 'json' in r.headers.get('Content-Type','') else raw
call('/admin/list',{},expected=403)
call('/admin/intake',{'open':True},True)
call('/nominations',{'name':'Synthetic','email':'synthetic@example.invalid','office':'president','kind':'self','contactConsent':True})
b=io.BytesIO();Image.new('RGB',(30,30),'white').save(b,'JPEG');photo=base64.b64encode(b.getvalue()).decode()
for office in ['president','vice_president','secretary','treasurer']:
 link=call('/admin/invite',{'name':'Synthetic '+office},True);invite=link['upload_link'].split('#invite=')[1]
 body={'invite':invite,'name':'Synthetic '+office,'affiliation':'Test','bio':'Test only','office':office,'photo':photo,'consent':True}
 call('/candidate/submit',body)
 c={'id':link['id'],'revision':1}
 call('/admin/sanitize',{**c,'photo':photo},True)
 call('/admin/approve',c,True)
assert len(call('/approved')['offices'])==4
# Fixed fixture credentials only; no random voting code generation.
call('/admin/voting/register',{'email':'fixture@example.invalid','code':'ABC'},True)
call('/admin/voting/register',{'email':'fixture@example.invalid','code':'XYZ'},True,409)
call('/admin/voting/results',{},True,409)
# Allow a fresh rate window before timed voting checks.
time.sleep(61-time.time()%60)
start=datetime.now(timezone.utc)+timedelta(seconds=3)
call('/admin/voting/schedule',{'opensAt':start.isoformat(),'closesAt':(start+timedelta(seconds=8)).isoformat()},True)
assert call('/candidate/profile',{'invite':invite})['locked']
call('/candidate/submit',body,expected=409)
choices={o['id']:'ABSTAIN' for o in call('/election')['offices']}
vote={'electionId':'cu-student-chapter-election','email':'fixture@example.invalid','token':'ABC','choices':choices}
call('/ballots',vote,expected=409)
time.sleep(3.2)
call('/ballots',{**vote,'choices':{}},expected=400)
with ThreadPoolExecutor(max_workers=4) as pool:
 responses=list(pool.map(lambda _:call('/ballots',vote),range(4)))
assert len({r['receipt'] for r in responses})==1
time.sleep(8)
assert call('/ballots',vote)['alreadyRecorded']
result=call('/admin/voting/results',{},True)
assert result['ballots']==1
assert all(c['ABSTAIN']==1 for c in result['counts'].values())
print('PASS: intake, photo, approval, schedule lock, concurrent one-vote enforcement, retry after close, and tally. Only fixed localhost fixtures used.')
