"""Private operator tool. Never sends email or creates voting codes."""
import argparse,base64,json,os,sys,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'backend'))
from candidates import clean_photo

def request(api,token,route,body,binary=False):
    req=urllib.request.Request(api.rstrip('/')+route,data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+token,'User-Agent':'ECS-Section-Admin/1.0'})
    with urllib.request.urlopen(req,timeout=45) as response:
        raw=response.read();return raw if binary else json.loads(raw)

def main():
    p=argparse.ArgumentParser();p.add_argument('--api',required=True);p.add_argument('--token-file',required=True)
    sub=p.add_subparsers(dest='command',required=True)
    l=sub.add_parser('list');l.add_argument('--output',required=True)
    i=sub.add_parser('invite');i.add_argument('--name',required=True);i.add_argument('--output',required=True)
    s=sub.add_parser('intake');s.add_argument('--open',action='store_true')
    for action in ['sanitize','shortlist','approve']:
        a=sub.add_parser(action);a.add_argument('--id',required=True);a.add_argument('--revision',required=True,type=int)
    schedule=sub.add_parser('schedule');schedule.add_argument('--opens-at',required=True);schedule.add_argument('--closes-at',required=True)
    result=sub.add_parser('results');result.add_argument('--output',required=True)
    unlock=sub.add_parser('unlock');unlock.add_argument('--email',required=True)
    a=p.parse_args();token=Path(a.token_file).read_text().strip()
    if not a.api.startswith('https://') and not a.api.startswith('http://127.0.0.1:'):raise ValueError('HTTPS required')
    body={k:getattr(a,k) for k in ['name','id','revision','open'] if hasattr(a,k)}
    if a.command=='sanitize':
        raw=request(a.api,token,'/admin/photo',body,True)
        body['photo']=base64.b64encode(clean_photo(base64.b64encode(raw).decode())).decode()
    route='/admin/'+a.command
    if a.command=='schedule':
        route='/admin/voting/schedule';body={'opensAt':a.opens_at,'closesAt':a.closes_at}
    if a.command=='results':route='/admin/voting/results'
    if a.command=='unlock':route='/admin/voting/unlock';body={'email':a.email}
    result=request(a.api,token,route,body)
    if hasattr(a,'output'):
        os.umask(0o077)
        with open(a.output,'x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
        print('Saved privately. No email sent.')
    else:print('Completed.')
if __name__=='__main__':main()
