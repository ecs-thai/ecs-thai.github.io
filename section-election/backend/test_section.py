import unittest,tempfile,json,io,base64,csv,time
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image
from server import initialize,connect,issue,cast,results
from candidates import invite,candidate_request,shortlist,approve
from nominations import receive,publish,set_intake
class SectionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.db=str(self.root/'section.db');self.config=json.loads((Path(__file__).parents[1]/'config.json').read_text());initialize(self.db,self.config)
 def tearDown(self):self.tmp.cleanup()
 def test_intake_closed_then_private(self):
  data={'name':'Test','email':'test@example.invalid','office':'chair','kind':'self','contactConsent':True}
  self.assertEqual(receive(self.db,data)[0],409)
  set_intake(self.db,True)
  self.assertEqual(receive(self.db,data)[0],200);self.assertEqual(receive(self.db,data)[0],200)
  self.assertEqual(receive(self.db,{**data,'kind':'nominate'})[0],400)
  db=connect(self.db);self.assertEqual(db.execute('SELECT count(*) FROM nominations').fetchone()[0],1);db.close()
 def test_two_stage_approval_and_reset(self):
  (self.root/'roster.csv').write_text('name,email\nTest,test@example.invalid\n');invite(self.db,self.root/'roster.csv',self.root/'links.csv','https://example.invalid')
  row=list(csv.DictReader((self.root/'links.csv').read_text().splitlines()))[0];secret=row['upload_link'].split('#invite=')[1];b=io.BytesIO();Image.new('RGB',(10,10),'red').save(b,'PNG')
  body={'invite':secret,'name':'Test','affiliation':'University','bio':'Bio','office':'chair','photo':base64.b64encode(b.getvalue()).decode(),'consent':True}
  self.assertEqual(candidate_request(self.db,'/candidate/submit',body)[0],200)
  with self.assertRaises(ValueError):approve(self.db,row['candidate_id'])
  shortlist(self.db,row['candidate_id']);publish(self.db,self.root/'before');self.assertEqual(json.loads((self.root/'before/approved.json').read_text())['offices'][0]['candidates'],[])
  approve(self.db,row['candidate_id']);publish(self.db,self.root/'after');public=json.loads((self.root/'after/approved.json').read_text());self.assertEqual(len(public['offices'][0]['candidates']),1);self.assertNotIn('invite',str(public));self.assertNotIn('email',str(public))
  candidate_request(self.db,'/candidate/submit',{**body,'office':'secretary','photo':''})
  with self.assertRaises(ValueError):approve(self.db,row['candidate_id'])
  publish(self.db,self.root/'reset');self.assertTrue(all(not o['candidates'] for o in json.loads((self.root/'reset/approved.json').read_text())['offices']))
 def test_members_at_large_ballots(self):
  now=round(time.time(),3);db=connect(self.db);c=json.loads(db.execute('SELECT config FROM settings').fetchone()[0]);c.update(mode='live',opensAt=datetime.fromtimestamp(now+100,timezone.utc).isoformat(),closesAt=datetime.fromtimestamp(now+200,timezone.utc).isoformat())
  for o in c['offices']:o['candidates']=[{'id':'a','name':'A'},{'id':'b','name':'B'}]
  db.execute('UPDATE settings SET config=?',(json.dumps(c),));db.close();(self.root/'voters.csv').write_text('name,email\nTest,test@example.invalid\n');issue(self.db,self.root/'voters.csv',self.root/'codes.csv');code=list(csv.DictReader((self.root/'codes.csv').read_text().splitlines()))[0]['voting_code']
  choices={o['id']:('a' if o['type']=='SINGLE' else {'a':'YES','b':'NO'}) for o in c['offices']};body={'electionId':c['electionId'],'email':'test@example.invalid','token':code,'choices':choices}
  self.assertEqual(cast(self.db,{**body,'choices':{**choices,'members_at_large':{'a':'YES'}}},now+150)[0],400)
  self.assertEqual(cast(self.db,body,now+150)[0],200);self.assertEqual(cast(self.db,body,now+150)[0],200)
  r=results(self.db,now+201);self.assertEqual(r['ballots'],1);self.assertEqual(r['counts']['members_at_large']['a']['YES'],1);self.assertEqual(r['counts']['members_at_large']['b']['NO'],1)
if __name__=='__main__':unittest.main()
