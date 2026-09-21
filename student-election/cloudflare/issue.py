"""Deferred operator workflow. Run only when explicitly authorized to issue voting codes."""
import argparse,csv,json,os,secrets
from pathlib import Path
from admin import request
p=argparse.ArgumentParser()
p.add_argument('--api',required=True);p.add_argument('--token-file',required=True)
p.add_argument('--roster');p.add_argument('--output',required=True);p.add_argument('--resume',action='store_true')
a=p.parse_args()
if not a.api.startswith('https://'):raise ValueError('HTTPS required')
token=Path(a.token_file).read_text().strip()
# Save credentials durably before registration, so a lost response can be retried.
if a.resume:
 with open(a.output,newline='') as f:rows=list(csv.DictReader(f))
else:
 if not a.roster:raise ValueError('Provide roster')
 with open(a.roster,encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
 emails=[r['email'].strip().lower() for r in rows]
 if not emails or len(set(emails))!=len(emails) or any('@' not in e for e in emails):raise ValueError('Use unique email addresses')
 for r,e in zip(rows,emails):r.update(email=e,voting_code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(3)))
 os.umask(0o077)
 with open(a.output,'x',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['name','email','voting_code'],extrasaction='ignore');w.writeheader();w.writerows(rows);f.flush();os.fsync(f.fileno())
import time,urllib.error
for r in rows:
 for attempt in range(3):
  try:
   request(a.api,token,'/admin/voting/register',{'email':r['email'],'code':r['voting_code']});break
  except urllib.error.HTTPError as e:
   if e.code==429 and attempt<2:time.sleep(60);continue
   raise
print('Registered. Private CSV retained. No emails sent.')
