"""Invitation-only candidate profiles. Photos remain private until approved/exported."""
import argparse,base64,binascii,csv,io,json,secrets,time,uuid,warnings
from pathlib import Path
from PIL import Image,ImageOps,UnidentifiedImageError
from server import connect,config_for,digest,stamp

def schema(db):
    db.execute('CREATE TABLE IF NOT EXISTS candidates(id TEXT PRIMARY KEY, office TEXT NOT NULL, invite_hash TEXT UNIQUE NOT NULL, expires REAL NOT NULL, profile TEXT NOT NULL, photo BLOB, submitted INTEGER NOT NULL DEFAULT 0, approved INTEGER NOT NULL DEFAULT 0)')

def invite(path,roster,output,base_url,days=14):
    with open(roster,encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    db=connect(path);schema(db);config=config_for(db)
    if config.get('opensAt') and time.time()>=stamp(config['opensAt']):raise ValueError('Voting has already opened')
    offices={o['id'] for o in config['offices']}
    if not rows or any((r.get('office','') and r['office'] not in offices) or '@' not in r.get('email','') for r in rows):raise ValueError('Use name,email columns; an optional office must be valid')
    with open(output,'x',encoding='utf-8',newline='') as f:
        import os
        os.chmod(output,0o600)
        try:
            db.execute('BEGIN IMMEDIATE');writer=csv.writer(f);writer.writerow(['candidate_id','name','email','office','upload_link'])
            for r in rows:
                ident=uuid.uuid4().hex;secret=secrets.token_urlsafe(32)
                db.execute('INSERT INTO candidates(id,office,invite_hash,expires,profile) VALUES(?,?,?,?,?)',(ident,r.get('office',''),digest(secret),time.time()+days*86400,json.dumps({'name':r.get('name',''),'affiliation':'Chulalongkorn University','bio':''})))
                writer.writerow([ident,r.get('name',''),r['email'],r.get('office',''),base_url+'#invite='+secret])
            f.flush();os.fsync(f.fileno());db.execute('COMMIT')
        except Exception:
            db.execute('ROLLBACK');Path(output).unlink(missing_ok=True);raise
        finally:db.close()

def clean_photo(encoded):
    if not isinstance(encoded,str) or len(encoded)>7_000_000:raise ValueError('photo')
    try:raw=base64.b64decode(encoded,validate=True)
    except binascii.Error:raise ValueError('photo')
    if len(raw)>5*1024*1024:raise ValueError('photo')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as im:
                if im.format not in ('JPEG','PNG') or im.width*im.height>20_000_000:raise ValueError('photo')
                im.load();im=ImageOps.exif_transpose(im).convert('RGB');im.thumbnail((1000,1000));out=io.BytesIO();im.save(out,format='JPEG',quality=88);return out.getvalue()
    except (UnidentifiedImageError,OSError,Image.DecompressionBombError,Image.DecompressionBombWarning):raise ValueError('photo')

def candidate_request(path,route,body):
    if not isinstance(body,dict) or not isinstance(body.get('invite'),str) or not 30<=len(body['invite'])<=100:return 403,{'error':'invalid_invite'}
    db=connect(path);schema(db)
    try:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT id,office,expires,profile,photo,submitted,approved FROM candidates WHERE invite_hash=?',(digest(body['invite']),)).fetchone()
        if not row or row[2]<time.time():return 403,{'error':'invalid_invite'}
        config=config_for(db);locked=bool(config.get('opensAt') and time.time()>=stamp(config['opensAt']))
        if route=='/candidate/profile':return 200,{'profile':json.loads(row[3]),'office':next((o for o in config['offices'] if o['id']==row[1]),None),'offices':config['offices'],'hasPhoto':row[4] is not None,'submitted':bool(row[5]),'approved':bool(row[6]),'locked':locked}
        if locked:return 409,{'error':'closed'}
        office=body.get('office')
        if not isinstance(office,str) or office not in {o['id'] for o in config['offices']}:return 400,{'error':'invalid_office'}
        profile={k:body.get(k,'').strip() if isinstance(body.get(k,''),str) else '' for k in ['name','affiliation','bio']}
        if not 1<=len(profile['name'])<=150 or not 1<=len(profile['affiliation'])<=200 or not 1<=len(profile['bio'])<=3000 or body.get('consent') is not True:return 400,{'error':'invalid_profile'}
        try:photo=clean_photo(body['photo']) if body.get('photo') else row[4]
        except ValueError:return 400,{'error':'invalid_photo'}
        if photo is None:return 400,{'error':'invalid_photo'}
        db.execute('UPDATE candidates SET office=?,profile=?,photo=?,submitted=1,approved=0 WHERE id=?',(office,json.dumps(profile),photo,row[0]));db.execute('COMMIT')
        return 200,{'status':'pending_review'}
    finally:
        if db.in_transaction:db.execute('ROLLBACK')
        db.close()

def export_profiles(path,out,approved=False):
    db=connect(path);schema(db);target=Path(out);target.mkdir(parents=True,exist_ok=False)
    rows=db.execute('SELECT id,office,profile,photo,approved FROM candidates WHERE submitted=1'+(' AND approved=1' if approved else '')).fetchall();profiles=[]
    for ident,office,profile,photo,ok in rows:
        filename=ident+'.jpg';(target/filename).write_bytes(photo);profiles.append({'id':ident,'office':office,**json.loads(profile),'photo':filename,'approved':bool(ok)})
    (target/'profiles.json').write_text(json.dumps(profiles,ensure_ascii=False,indent=2));db.close()

def approve(path,ident):
    db=connect(path);schema(db)
    c=config_for(db)
    if c.get('opensAt') and time.time()>=stamp(c['opensAt']):raise ValueError('Election already open')
    if db.execute('UPDATE candidates SET approved=1 WHERE id=? AND submitted=1',(ident,)).rowcount!=1:raise ValueError('Candidate has not submitted a profile')
    db.close()

def schedule(path,opens,closes,api,output,photos):
    if not time.time()<stamp(opens)<stamp(closes) or not api.startswith('https://'):raise ValueError('Set future timezone-aware dates and an HTTPS API URL')
    db=connect(path);schema(db)
    try:
        db.execute('BEGIN IMMEDIATE');config=config_for(db)
        if db.execute('SELECT COUNT(*) FROM ballots').fetchone()[0] or (config.get('opensAt') and time.time()>=stamp(config['opensAt'])):raise ValueError('Cannot change an election that has opened')
        profiles=db.execute('SELECT id,office,profile FROM candidates WHERE approved=1').fetchall()
        for o in config['offices']:
            o['candidates']=[{'id':i,**json.loads(p),'photo':photos.rstrip('/')+'/'+i+'.jpg'} for i,office,p in profiles if office==o['id']]
            if not o['candidates']:raise ValueError('Every office needs an approved candidate')
        config.update(mode='live',opensAt=opens,closesAt=closes,apiBase=api.rstrip('/'))
        # Creation with x prevents silently replacing an existing public configuration.
        public={k:v for k,v in config.items() if k!='credentialKey'}
        with open(output,'x',encoding='utf-8') as f:json.dump(public,f,ensure_ascii=False,indent=2)
        db.execute('UPDATE settings SET config=?',(json.dumps(config),));db.execute('COMMIT')
    finally:
        if db.in_transaction:db.execute('ROLLBACK')
        db.close()

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);sub=p.add_subparsers(dest='command',required=True)
    i=sub.add_parser('invite');i.add_argument('--roster',required=True);i.add_argument('--output',required=True);i.add_argument('--url',default='https://ecs-thai.github.io/student-election/candidate.html');i.add_argument('--days',type=int,default=14)
    e=sub.add_parser('export');e.add_argument('--output',required=True);e.add_argument('--approved-only',action='store_true')
    a=sub.add_parser('approve');a.add_argument('--id',required=True)
    s=sub.add_parser('schedule');s.add_argument('--opens',required=True);s.add_argument('--closes',required=True);s.add_argument('--api',required=True);s.add_argument('--output',required=True);s.add_argument('--photos',default='photos')
    args=p.parse_args()
    if args.command=='invite':invite(args.db,args.roster,args.output,args.url,args.days)
    elif args.command=='export':export_profiles(args.db,args.output,args.approved_only)
    elif args.command=='approve':approve(args.db,args.id)
    else:schedule(args.db,args.opens,args.closes,args.api,args.output,args.photos)
if __name__=='__main__':main()
