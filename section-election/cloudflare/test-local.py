"""Exercise only a LOCAL Wrangler service with synthetic candidate data."""
import base64,io,json,sys,urllib.request,urllib.error,uuid
from pathlib import Path
from PIL import Image
API='http://127.0.0.1:8790';token=Path(__file__).with_name('.dev.vars').read_text().strip().split('=',1)[1]
def call(route,body=None,admin=False,method='POST',expected=200):
 headers={'Content-Type':'application/json','Origin':'https://ecs-thai.github.io'}
 if admin:headers['Authorization']='Bearer '+token
 req=urllib.request.Request(API+route,data=json.dumps(body or {}).encode() if method=='POST' else None,headers=headers,method=method)
 try:r=urllib.request.urlopen(req)
 except urllib.error.HTTPError as e:r=e
 assert r.status==expected,(route,r.status,r.read().decode());raw=r.read()
 return json.loads(raw) if 'json' in r.headers.get('Content-Type','') else raw
call('/admin/list',expected=403)
call('/ballots',expected=404)
call('/admin/intake',{'open':True},True)
call('/nominations',{'name':'Test','email':str(uuid.uuid4())+'@example.invalid','office':'chair','kind':'self','contactConsent':True})
link=call('/admin/invite',{'name':'Local test'},True);invite=link['upload_link'].split('#invite=')[1]
call('/candidate/profile',{'invite':'x'*64},expected=403)
b=io.BytesIO();Image.new('RGB',(20,20),'white').save(b,'JPEG');photo=base64.b64encode(b.getvalue()).decode()
body={'invite':invite,'name':'Local test','affiliation':'Example university','bio':'Local test only','office':'chair','photo':photo,'consent':True}
call('/candidate/submit',{**body,'consent':False},expected=400)
call('/candidate/submit',body)
assert call('/candidate/profile',{'invite':invite})['hasPhoto']
c={'id':link['id'],'revision':1}
call('/admin/approve',c,True,expected=400)
call('/admin/sanitize',{**c,'photo':photo},True)
call('/admin/approve',c,True,expected=409)
call('/admin/shortlist',c,True)
call('/admin/approve',c,True)
approved=call('/approved',method='GET');assert invite not in json.dumps(approved)
assert any(x['id']==link['id'] for o in approved['offices'] for x in o['candidates'])
assert call('/photos/'+link['id'],method='GET').startswith(b'\xff\xd8')
call('/candidate/submit',{**body,'bio':'Edited','photo':''})
call('/photos/'+link['id'],method='GET',expected=404)
call('/admin/approve',c,True,expected=409)
call('/admin/intake',{'open':False},True)
print('Local D1/R2 flow passed: nomination, private image, two-stage review, revision protection, and unpublication after editing. No voting codes or emails.')
