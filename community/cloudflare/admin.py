"""Private community administration. Does not send email."""
import argparse,json,os,urllib.request
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--api',required=True);p.add_argument('--token-file',required=True);p.add_argument('--output',required=True)
s=p.add_subparsers(dest='command',required=True);s.add_parser('list');i=s.add_parser('invite');i.add_argument('--name',required=True);i.add_argument('--email',required=True)
a=p.parse_args()
if not a.api.startswith('https://'):raise ValueError('HTTPS required')
body={k:getattr(a,k) for k in ['name','email'] if hasattr(a,k)}
req=urllib.request.Request(a.api+'/admin/'+a.command,data=json.dumps(body).encode(),headers={'Content-Type':'application/json','User-Agent':'ECS-Community-Admin/1.0','Authorization':'Bearer '+Path(a.token_file).read_text().strip()})
with urllib.request.urlopen(req,timeout=30) as r:result=json.load(r)
os.umask(0o077)
with open(a.output,'x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print('Saved privately. No emails sent.')
