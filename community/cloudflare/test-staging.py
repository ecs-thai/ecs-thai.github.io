"""Tests only isolated staging, never production. No emails sent."""
import json,urllib.request,urllib.error,uuid
from pathlib import Path
API='https://ecs-community-staging.ecs-thailand-election.workers.dev'
admin=(Path.home()/'ecs-community-private/staging-token').read_text().strip()
def call(path,body=None,token='',expected=200):
 headers={'Content-Type':'application/json','User-Agent':'ECS-Community-Test/1.0','Origin':'https://ecs-thai.github.io'}
 if token:headers['Authorization']='Bearer '+token
 req=urllib.request.Request(API+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
 try:r=urllib.request.urlopen(req,timeout=30)
 except urllib.error.HTTPError as e:r=e
 raw=r.read();assert r.status==expected,(path,r.status,raw[:150]);return json.loads(raw)
call('/admin/list',{},expected=403)
suffix=str(uuid.uuid4())
call('/access',{'name':'Test member','email':suffix+'@example.invalid','consent':True})
a=call('/admin/invite',{'name':'Test member','email':suffix+'@example.invalid'},admin)['link'].split('#access=')[1]
b=call('/admin/invite',{'name':'Other member','email':'other-'+suffix+'@example.invalid'},admin)['link'].split('#access=')[1]
base={'title':'Synthetic opportunity','institution':'Test university','description':'Test only','contact':'test@example.invalid','kind':'opportunity','category':'phd','deadline':'2099-12-31','consent':True}
call('/save',base,expected=403)
call('/save',{**base,'link':'javascript:alert(1)'},a,400)
p=call('/save',base,a)['id']
assert not any(x['id']==p for x in call('/posts')['posts'])
call('/save',{**base,'id':p,'revision':1},b,409)
call('/admin/review',{'id':p,'revision':1,'status':'approved'},admin)
assert any(x['id']==p for x in call('/posts')['posts'])
call('/save',{**base,'id':p,'revision':1,'title':'Edited'},a)
assert not any(x['id']==p for x in call('/posts')['posts'])
call('/admin/review',{'id':p,'revision':1,'status':'approved'},admin,409)
call('/admin/review',{'id':p,'revision':2,'status':'approved'},admin)
call('/report',{'id':p,'reason':'Synthetic report'})
call('/close',{'id':p},a)
assert next(x for x in call('/posts')['posts'] if x['id']==p)['archived']
for kind in ['lab','event']:
 body={**base,'kind':kind,'title':'Synthetic '+kind}
 if kind=='event':body.update(start='2099-01-01T09:00:00+07:00',end='2099-01-01T10:00:00+07:00')
 post=call('/save',body,a)['id']
 call('/admin/review',{'id':post,'revision':1,'status':'approved'},admin)
 assert any(x['id']==post for x in call('/posts')['posts'])
data=call('/admin/list',{},admin)
member=next(m for m in data['members'] if m['email']==suffix+'@example.invalid')
call('/admin/revoke',{'id':member['id']},admin)
call('/mine',{},a,403)
print('PASS: three post types, ownership, approval, edit re-review, stale review rejection, close/archive, reports, unsafe URL rejection and revocation.')
