"""Private nomination intake and approved ballot export for ECS Thailand Section."""
import argparse,csv,json,secrets,time,re
from pathlib import Path
from server import connect,config_for
from candidates import schema

def receive(path,body):
    if not isinstance(body,dict):return 400,{'error':'invalid_request'}
    db=connect(path)
    try:
        config=config_for(db)
        if not config.get('nominationsOpen'):return 409,{'error':'closed'}
        fields={k:body.get(k,'').strip() if isinstance(body.get(k,''),str) else '' for k in ['name','email','office','nominatorName','nominatorEmail','kind']}
        email=lambda x:len(x)<=254 and re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',x)
        if not 1<=len(fields['name'])<=150 or not email(fields['email']) or fields['office'] not in {o['id'] for o in config['offices']} or fields['kind'] not in ['self','nominate'] or body.get('contactConsent') is not True:return 400,{'error':'invalid_request'}
        if fields['kind']=='nominate' and (not 1<=len(fields['nominatorName'])<=150 or not email(fields['nominatorEmail'])):return 400,{'error':'invalid_request'}
        if fields['kind']=='self':fields['nominatorName']=fields['name'];fields['nominatorEmail']=fields['email']
        fields['email']=fields['email'].lower();fields['nominatorEmail']=fields['nominatorEmail'].lower()
        db.execute('CREATE TABLE IF NOT EXISTS nominations(id TEXT PRIMARY KEY,email TEXT NOT NULL,office TEXT NOT NULL,data TEXT NOT NULL,UNIQUE(email,office))')
        db.execute('INSERT OR IGNORE INTO nominations VALUES(?,?,?,?)',(secrets.token_hex(16),fields['email'],fields['office'],json.dumps(fields)))
        return 200,{'status':'received'}
    finally:db.close()

def export_requests(path,output):
    db=connect(path)
    with open(output,'x',encoding='utf-8',newline='') as f:
        import os
        os.chmod(output,0o600);writer=csv.DictWriter(f,fieldnames=['name','email','office','kind','nominatorName','nominatorEmail']);writer.writeheader()
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='nominations'").fetchone():
            for row in db.execute('SELECT data FROM nominations'):writer.writerow(json.loads(row[0]))
    db.close()

def publish(path,output):
    db=connect(path);schema(db);config=config_for(db);target=Path(output);target.mkdir(parents=True,exist_ok=False);offices=[]
    for o in config['offices']:
        candidates=[]
        for ident,profile,photo in db.execute('SELECT id,profile,photo FROM candidates WHERE office=? AND approved=1 AND shortlisted=1',(o['id'],)):
            (target/'photos').mkdir(exist_ok=True);(target/'photos'/f'{ident}.jpg').write_bytes(photo)
            candidates.append({'id':ident,**json.loads(profile),'photo':f'photos/{ident}.jpg'})
        offices.append({'id':o['id'],'title':o['en'],'th':o['th'],'type':o.get('type','SINGLE'),'candidates':candidates})
    public={'electionId':config['electionId'],'title':'ECS Thailand Section · Executive Committee Election','offices':offices}
    (target/'approved.json').write_text(json.dumps(public,ensure_ascii=False,indent=2));db.close()

def set_intake(path, opened):
    db=connect(path)
    try:
        config=config_for(db);config['nominationsOpen']=opened
        db.execute('UPDATE settings SET config=?',(json.dumps(config),))
    finally:db.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',required=True)
    sub=p.add_subparsers(dest='command',required=True)
    for command in ['export-requests','publish']:
        sub.add_parser(command).add_argument('--output',required=True)
    intake=sub.add_parser('intake');choice=intake.add_mutually_exclusive_group(required=True)
    choice.add_argument('--open',action='store_true');choice.add_argument('--close',action='store_true')
    args=p.parse_args()
    if args.command=='intake':set_intake(args.db,args.open)
    else:(export_requests if args.command=='export-requests' else publish)(args.db,args.output)
