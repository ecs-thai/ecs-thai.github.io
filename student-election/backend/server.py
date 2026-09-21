"""Small, single-election service. Run behind an HTTPS reverse proxy for live use."""
import argparse,csv,hashlib,hmac,json,secrets,sqlite3,time,os
from collections import defaultdict,deque
from threading import Lock
from pathlib import Path
from datetime import datetime
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer


def connect(path):
    db=sqlite3.connect(path,timeout=15,isolation_level=None)
    db.execute('PRAGMA busy_timeout=15000')
    return db

def stamp(value):
    dt=datetime.fromisoformat(value.replace('Z','+00:00'))
    if dt.tzinfo is None: raise ValueError('Dates must include a timezone')
    return dt.timestamp()

def initialize(path,config):
    if Path(path).exists(): raise ValueError('Database already exists; use a new path for a new election')
    if config.get('mode') != 'draft' and (not config.get('opensAt') or not config.get('closesAt') or stamp(config['opensAt'])>=stamp(config['closesAt'])): raise ValueError('Set valid opening and closing dates with timezones')
    offices=config['offices']
    if not offices or len({o['id'] for o in offices})!=len(offices): raise ValueError('Office IDs must be unique')
    for o in offices:
        ids=[c['id'] for c in o['candidates']]
        if (not ids and config.get('mode') != 'draft') or len(set(ids))!=len(ids) or 'ABSTAIN' in ids: raise ValueError('Each office needs unique candidates; ABSTAIN is reserved')
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    db=connect(path)
    db.executescript('CREATE TABLE settings(config TEXT NOT NULL); CREATE TABLE voters(identity_hash TEXT PRIMARY KEY, token_hash TEXT NOT NULL, receipt TEXT, failures INTEGER NOT NULL DEFAULT 0); CREATE TABLE ballots(id TEXT PRIMARY KEY, choices TEXT NOT NULL);')
    config={**config,'credentialKey':secrets.token_hex(32)}
    db.execute('INSERT INTO settings VALUES(?)',(json.dumps(config),));db.close();os.chmod(path,0o600)

def config_for(db):return json.loads(db.execute('SELECT config FROM settings').fetchone()[0])
def digest(text):return hashlib.sha256(text.encode()).hexdigest()

CODE_ALPHABET='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
def code_hash(config,email,code):
    return hmac.new(bytes.fromhex(config['credentialKey']),(email+'\0'+code).encode(),hashlib.sha256).hexdigest()

def issue(path,roster,output):
    # Reject duplicate issuance even if the same roster is imported again.
    with open(roster,encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    emails=[r['email'].strip().lower() for r in rows]
    if not emails or any('@' not in e for e in emails) or len(set(emails))!=len(emails): raise ValueError('Use unique email addresses in an email column')
    db=connect(path)
    config=config_for(db)
    if config.get('opensAt') and time.time()>=stamp(config['opensAt']):
        db.close();raise ValueError('Issue codes before voting opens')
    with open(output,'x',encoding='utf-8',newline='') as f:
        os.chmod(output,0o600)
        try:
            db.execute('BEGIN IMMEDIATE');writer=csv.writer(f);writer.writerow(['name','email','voting_code'])
            for row,email in zip(rows,emails):
                token=''.join(secrets.choice(CODE_ALPHABET) for _ in range(3))
                db.execute('INSERT INTO voters(identity_hash,token_hash) VALUES(?,?)',(digest(email),code_hash(config,email,token)))
                writer.writerow([row.get('name',''),email,token])
            f.flush();os.fsync(f.fileno());db.execute('COMMIT')
        except Exception:
            db.execute('ROLLBACK');Path(output).unlink(missing_ok=True);raise
        finally:db.close()

def cast(path,body,now=None):
    if not isinstance(body,dict) or not isinstance(body.get('email'),str) or not isinstance(body.get('token'),str):return 403,{'error':'invalid_credentials'}
    email=body['email'].strip().lower();code=body['token'].strip().upper()
    if len(email)>254 or len(code)!=3:return 403,{'error':'invalid_credentials'}
    db=connect(path)
    try:
        db.execute('BEGIN IMMEDIATE');config=config_for(db)
        if body.get('electionId')!=config['electionId']:return 400,{'error':'invalid_ballot'}
        row=db.execute('SELECT receipt,token_hash,failures FROM voters WHERE identity_hash=?',(digest(email),)).fetchone()
        if row is None or row[2]>=5:return 403,{'error':'invalid_credentials'}
        if not hmac.compare_digest(row[1],code_hash(config,email,code)):
            db.execute('UPDATE voters SET failures=failures+1 WHERE identity_hash=?',(digest(email),));db.execute('COMMIT')
            return 403,{'error':'invalid_credentials'}
        # A lost response can be retried safely, including after the election closes.
        if row[0]:return 200,{'receipt':row[0],'alreadyRecorded':True}
        now=time.time() if now is None else now
        if config.get('mode')=='draft' or not config.get('opensAt') or not stamp(config['opensAt'])<=now<stamp(config['closesAt']):return 409,{'error':'closed'}
        votes=body.get('choices')
        if not isinstance(votes,dict) or set(votes)!={o['id'] for o in config['offices']}:return 400,{'error':'invalid_ballot'}
        for o in config['offices']:
            if not isinstance(votes[o['id']],str) or votes[o['id']] not in ['ABSTAIN']+[c['id'] for c in o['candidates']]:return 400,{'error':'invalid_ballot'}
        receipt=secrets.token_hex(12)
        db.execute('INSERT INTO ballots VALUES(?,?)',(secrets.token_hex(24),json.dumps(votes)))
        db.execute('UPDATE voters SET receipt=? WHERE identity_hash=?',(receipt,digest(email)))
        db.execute('COMMIT');return 200,{'receipt':receipt,'alreadyRecorded':False}
    finally:
        if db.in_transaction:db.execute('ROLLBACK')
        db.close()

def results(path,now=None):
    db=connect(path)
    try:
        config=config_for(db)
        if not config.get('closesAt') or (time.time() if now is None else now)<stamp(config['closesAt']):raise ValueError('Results are available only after voting closes')
        counts={o['id']:{c['id']:0 for c in o['candidates']}|{'ABSTAIN':0} for o in config['offices']}
        rows=db.execute('SELECT choices FROM ballots').fetchall()
        for row in rows:
            for office,candidate in json.loads(row[0]).items():counts[office][candidate]+=1
        return {'electionId':config['electionId'],'eligible':db.execute('SELECT COUNT(*) FROM voters').fetchone()[0],'ballots':len(rows),'counts':counts,'note':'Counts only. Apply the chapter election rules, including ties and uncontested seats, before certifying winners.'}
    finally:db.close()

class RateLimiter:
    def __init__(self):self.requests=defaultdict(deque);self.lock=Lock()
    def allow(self,key):
        now=time.monotonic()
        with self.lock:
            for old in list(self.requests):
                if not self.requests[old] or self.requests[old][-1]<now-60:del self.requests[old]
            bucket=self.requests[key]
            while bucket and bucket[0]<now-60:bucket.popleft()
            if len(bucket)>=30:return False
            bucket.append(now);return True

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass # Do not log voting requests or credentials.
    def reply(self,status,data):
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Access-Control-Allow-Origin',self.server.origin);self.send_header('Vary','Origin');self.end_headers();self.wfile.write(json.dumps(data).encode())
    def allowed(self):return self.headers.get('Origin')==self.server.origin
    def do_OPTIONS(self):
        if not self.allowed():return self.reply(403,{'error':'origin'})
        self.send_response(204);self.send_header('Access-Control-Allow-Origin',self.server.origin);self.send_header('Access-Control-Allow-Methods','GET, POST, OPTIONS');self.send_header('Access-Control-Allow-Headers','Content-Type');self.end_headers()
    def do_GET(self):
        if self.path!='/election':return self.reply(404,{'error':'not_found'})
        db=connect(self.server.dbpath)
        try:config=config_for(db)
        finally:db.close()
        self.reply(200,{k:config[k] for k in ['electionId','chapter','opensAt','closesAt','offices']})
    def do_POST(self):
        if not self.allowed():return self.reply(403,{'error':'origin'})
        if self.path not in ['/ballots','/candidate/profile','/candidate/submit']:return self.reply(404,{'error':'not_found'})
        if not self.server.limiter.allow(self.client_address[0]):return self.reply(429,{'error':'rate_limited'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=(7_100_000 if self.path=='/candidate/submit' else 16384) or self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.reply(400,{'error':'invalid_request'})
            self.connection.settimeout(10)
            body=json.loads(self.rfile.read(size))
            if self.path=='/ballots':status,data=cast(self.server.dbpath,body)
            else:
                from candidates import candidate_request
                status,data=candidate_request(self.server.dbpath,self.path,body)
            self.reply(status,data)
        except (ValueError,TimeoutError):self.reply(400,{'error':'invalid_request'})
        except sqlite3.Error:self.reply(503,{'error':'retry'})
        except ImportError:self.reply(503,{'error':'service_unavailable'})

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);sub=p.add_subparsers(dest='command',required=True)
    init=sub.add_parser('init');init.add_argument('--config',required=True)
    codes=sub.add_parser('issue');codes.add_argument('--roster',required=True);codes.add_argument('--output',required=True)
    sub.add_parser('results')
    unlock=sub.add_parser('unlock');unlock.add_argument('--email',required=True)
    serve=sub.add_parser('serve');serve.add_argument('--origin',default='https://ecs-thai.github.io');serve.add_argument('--port',type=int,default=8766)
    args=p.parse_args()
    if args.command=='init':initialize(args.db,json.loads(Path(args.config).read_text()))
    elif args.command=='issue':issue(args.db,args.roster,args.output)
    elif args.command=='unlock':
        db=connect(args.db);db.execute('UPDATE voters SET failures=0 WHERE identity_hash=?',(digest(args.email.strip().lower()),));db.close()
    elif args.command=='results':print(json.dumps(results(args.db),ensure_ascii=False,indent=2))
    else:
        if not Path(args.db).is_file():raise ValueError('Initialize the election first')
        server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.dbpath=args.db;server.origin=args.origin;server.limiter=RateLimiter()
        print(f'Local API: http://127.0.0.1:{args.port}');server.serve_forever()
if __name__=='__main__':main()
