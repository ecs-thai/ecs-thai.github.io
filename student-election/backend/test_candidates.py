import unittest,tempfile,json,csv,base64,io,time
from pathlib import Path
from PIL import Image
from server import initialize,connect,config_for
from datetime import datetime,timezone
from candidates import invite,candidate_request,export_profiles,approve,schedule
from prepare_mail import prepare
class CandidateTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.db=str(self.root/'election.db');config=json.loads((Path(__file__).parents[1]/'config.json').read_text());initialize(self.db,config)
  (self.root/'invite.csv').write_text('name,email,office\nTest,test@example.invalid,president\n');invite(self.db,self.root/'invite.csv',self.root/'links.csv','https://example.invalid/candidate.html')
  self.row=list(csv.DictReader((self.root/'links.csv').read_text().splitlines()))[0];self.key=self.row['upload_link'].split('#invite=')[1]
  b=io.BytesIO();Image.new('RGB',(20,20),'red').save(b,'PNG');self.body={'invite':self.key,'office':'president','name':'Test','affiliation':'CU','bio':'My biography','photo':base64.b64encode(b.getvalue()).decode(),'consent':True}
 def tearDown(self):self.tmp.cleanup()
 def test_invitation_auth_and_private_export(self):
  self.assertEqual(candidate_request(self.db,'/candidate/profile',{'invite':'bad'*20})[0],403)
  self.assertEqual(candidate_request(self.db,'/candidate/submit',self.body)[0],200)
  export_profiles(self.db,self.root/'public',True);self.assertEqual(json.loads((self.root/'public/profiles.json').read_text()),[])
  approve(self.db,self.row['candidate_id']);export_profiles(self.db,self.root/'approved',True);self.assertEqual(len(json.loads((self.root/'approved/profiles.json').read_text())),1)
  self.assertEqual(candidate_request(self.db,'/candidate/submit',{**self.body,'bio':'Updated','photo':''})[0],200)
  export_profiles(self.db,self.root/'updated',True);self.assertEqual(json.loads((self.root/'updated/profiles.json').read_text()),[])
 def test_upload_validation_and_consent(self):
  for changes in [{'consent':False},{'photo':base64.b64encode(b'<svg>bad</svg>').decode()},{'bio':'x'*3001}]:self.assertEqual(candidate_request(self.db,'/candidate/submit',{**self.body,**changes})[0],400)
 def test_expiry(self):
  db=connect(self.db);db.execute('UPDATE candidates SET expires=?',(time.time()-1,));db.close();self.assertEqual(candidate_request(self.db,'/candidate/submit',self.body)[0],403)
 def test_schedule_requires_approved_candidates(self):
  opens=datetime.fromtimestamp(time.time()+3600,timezone.utc).isoformat();closes=datetime.fromtimestamp(time.time()+7200,timezone.utc).isoformat()
  with self.assertRaises(ValueError):schedule(self.db,opens,closes,'https://example.invalid',self.root/'public.json','photos')
  self.assertFalse((self.root/'public.json').exists())
  db=connect(self.db);config=config_for(db);config['offices']=config['offices'][:1];db.execute('UPDATE settings SET config=?',(json.dumps(config),));db.close()
  candidate_request(self.db,'/candidate/submit',self.body);approve(self.db,self.row['candidate_id']);schedule(self.db,opens,closes,'https://example.invalid',self.root/'public.json','photos')
  public=json.loads((self.root/'public.json').read_text());self.assertNotIn('credentialKey',public);self.assertEqual(public['mode'],'live');self.assertEqual(len(public['offices'][0]['candidates']),1)
 def test_candidate_selects_and_changes_office(self):
  self.assertEqual(candidate_request(self.db,'/candidate/submit',{**self.body,'office':'treasurer'})[0],200)
  status,result=candidate_request(self.db,'/candidate/profile',{'invite':self.key})
  self.assertEqual(result['office']['id'],'treasurer');self.assertEqual(len(result['offices']),4)
  approve(self.db,self.row['candidate_id'])
  self.assertEqual(candidate_request(self.db,'/candidate/submit',{**self.body,'office':'secretary','photo':''})[0],200)
  _,result=candidate_request(self.db,'/candidate/profile',{'invite':self.key});self.assertFalse(result['approved']);self.assertEqual(result['office']['id'],'secretary')
 def test_invalid_office_rejected(self):
  for office in ['',None,'unknown']:
   self.assertEqual(candidate_request(self.db,'/candidate/submit',{**self.body,'office':office})[0],400)
 def test_invite_without_preassigned_office(self):
  (self.root/'unassigned.csv').write_text('name,email\nTest,new@example.invalid\n')
  invite(self.db,self.root/'unassigned.csv',self.root/'unassigned-links.csv','https://example.invalid/candidate.html')
  row=list(csv.DictReader((self.root/'unassigned-links.csv').read_text().splitlines()))[0]
  status,result=candidate_request(self.db,'/candidate/profile',{'invite':row['upload_link'].split('#invite=')[1]})
  self.assertEqual(status,200);self.assertIsNone(result['office']);self.assertEqual(len(result['offices']),4)
 def test_private_mail_drafts(self):
  prepare(self.root/'links.csv',self.root/'mail','organizer@example.invalid','candidates');self.assertIn(b'To: test@example.invalid',(self.root/'mail/0001.eml').read_bytes())
if __name__=='__main__':unittest.main()
