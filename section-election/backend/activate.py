"""Connect the public forms after verifying the deployed intake service."""
import argparse,json,urllib.request
from pathlib import Path
from urllib.parse import urlparse

def activate(api,config_path):
    api=api.rstrip('/')
    u=urlparse(api)
    if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment:
        raise ValueError('Use the HTTPS service URL without credentials, query, or fragment')
    with urllib.request.urlopen(urllib.request.Request(api+'/health',headers={'User-Agent':'ECS-Section-Admin/1.0'}),timeout=20) as response:
        if json.load(response).get('status')!='ok':raise ValueError('Service health check failed')
    with urllib.request.urlopen(urllib.request.Request(api+'/intake',headers={'User-Agent':'ECS-Section-Admin/1.0'}),timeout=20) as response:
        opened=json.load(response).get('nominationsOpen') is True
    path=Path(config_path);config=json.loads(path.read_text())
    # Only connect intake; never change voting mode, schedule, or candidate lists.
    config.update(apiBase=api,nominationsOpen=opened)
    path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--api',required=True);p.add_argument('--config',default=str(Path(__file__).parents[1]/'config.json'));a=p.parse_args();activate(a.api,a.config)
