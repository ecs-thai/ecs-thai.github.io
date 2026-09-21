import unittest,tempfile,json,csv,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from server import initialize,issue,cast,results,connect
class ElectionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.db=str(self.root/'vote.sqlite');self.now=time.time()
  config=json.loads((Path(__file__).parents[1]/'sample.json').read_text());config['opensAt']=datetime.fromtimestamp(self.now+100,timezone.utc).isoformat();config['closesAt']=datetime.fromtimestamp(self.now+200,timezone.utc).isoformat();self.config=config
  initialize(self.db,config);(self.root/'roster.csv').write_text('email\ntest@example.invalid\n');issue(self.db,self.root/'roster.csv',self.root/'codes.csv');self.token=list(csv.DictReader((self.root/'codes.csv').read_text().splitlines()))[0]['voting_code'];self.body={'token':self.token,'electionId':config['electionId'],'choices':{o['id']:'ABSTAIN' for o in config['offices']}}
 def tearDown(self):self.tmp.cleanup()
 def test_atomic_retry(self):
  with ThreadPoolExecutor(max_workers=8) as pool:r=list(pool.map(lambda _:cast(self.db,self.body,self.now+150),range(12)))
  self.assertTrue(all(x[0]==200 for x in r));self.assertEqual(len({x[1]['receipt'] for x in r}),1);self.assertEqual(results(self.db,self.now+201)['ballots'],1)
  self.assertEqual(cast(self.db,self.body,self.now+201)[0],200)
 def test_invalid_does_not_consume_code(self):
  bad={**self.body,'choices':{'president':'unknown'}};self.assertEqual(cast(self.db,bad,self.now+150)[0],400);self.assertEqual(cast(self.db,self.body,self.now+150)[0],200)
 def test_window_and_results(self):
  self.assertEqual(cast(self.db,self.body,self.now)[0],409);self.assertEqual(cast(self.db,self.body,self.now+200)[0],409)
  with self.assertRaises(ValueError):results(self.db,self.now+150)
 def test_wrong_token_and_election(self):
  self.assertEqual(cast(self.db,{**self.body,'token':'x'*40},self.now+150)[0],403);self.assertEqual(cast(self.db,{**self.body,'electionId':'other'},self.now+150)[0],400)
 def test_duplicate_roster(self):
  with self.assertRaises(Exception):issue(self.db,self.root/'roster.csv',self.root/'duplicate.csv')
  db=connect(self.db);self.assertEqual(db.execute('SELECT count(*) FROM voters').fetchone()[0],1);db.close()
 def test_choice_tally(self):
  for o in self.config['offices']:self.body['choices'][o['id']]=o['candidates'][0]['id']
  cast(self.db,self.body,self.now+150);r=results(self.db,self.now+201)
  for o in self.config['offices']:self.assertEqual(r['counts'][o['id']][o['candidates'][0]['id']],1)
if __name__=='__main__':unittest.main()
