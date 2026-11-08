import json,unittest
import test_desktop_trial_export as fixtures
from tomeris_trial_export import dataset,export
from tomeris_research_trials import digest

class ExposureTests(unittest.TestCase):
 def setUp(self):
  self.fixture=fixtures.ExportTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
  self.root=self.fixture.root;self.manifest=self.fixture.manifest
 def change(self,index,mutation):
  entry=self.manifest[index];path=self.root/entry['record'];env=json.loads(path.read_text(encoding='utf-8'))
  mutation(env['record']);env['sha256']=digest(env['record']);path.write_text(json.dumps(env),encoding='utf-8')
  path=self.root/entry['review'];review=json.loads(path.read_text(encoding='utf-8'));review['record_sha256']=env['sha256'];path.write_text(json.dumps(review),encoding='utf-8')
 def test_lower_candidate_cross_split_blocks_output(self):
  self.change(0,lambda r:r['candidates'].append(dict(url='https://example.org/2')))
  output=self.root/'output.json'
  with self.assertRaises(ValueError):export(self.root,self.manifest,output)
  self.assertFalse(output.exists())
 def test_failed_page_cross_split_is_also_exposure(self):
  self.change(0,lambda r:r['pages'].append(dict(url='https://example.org/2',status='failed',page=None)))
  with self.assertRaises(ValueError):dataset(self.root,self.manifest)
 def test_lower_rank_and_resolved_page_url(self):
  self.change(0,lambda r:r['rankings']['search_order'].append('https://example.org/2'))
  with self.assertRaises(ValueError):dataset(self.root,self.manifest)
  self.change(0,lambda r:r['rankings']['search_order'].pop())
  self.change(0,lambda r:r['pages'][0]['page'].update(url='https://example.org/2'))
  with self.assertRaises(ValueError):dataset(self.root,self.manifest)
 def test_shared_material_within_training_allowed(self):
  self.change(0,lambda r:r['candidates'].append(dict(url='https://example.org/1')))
  self.assertEqual(len(dataset(self.root,self.manifest)),4)
 def test_malformed_candidate_not_ignored(self):
  self.change(0,lambda r:r['candidates'].append(dict(url=None)))
  with self.assertRaises(ValueError):dataset(self.root,self.manifest)
