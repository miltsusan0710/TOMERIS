import json,unittest
from pathlib import Path
import test_desktop_trial_export as fixtures
from tomeris_trial_export import export
from tomeris_experiment_view import run,summary,save

class ExperimentViewTests(unittest.TestCase):
 def setUp(self):
  self.fixture=fixtures.ExportTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
  self.root=self.fixture.root;self.path=self.root/'dataset.json'
  export(self.root,self.fixture.manifest,self.path)
 def test_reviewed_roundtrip_does_not_modify_sources(self):
  before={p.name:p.read_bytes() for p in self.root.iterdir()}
  result=run(self.path,self.root)
  self.assertTrue(result['source_verified']);self.assertFalse(result['production_enabled'])
  self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.iterdir()})
  self.assertIn('正答率ではありません',summary(result))
 def test_modified_rewards_rejected(self):
  rows=json.loads(self.path.read_text(encoding='utf-8'))
  rows[0]['rewards']={a:0 for a in rows[0]['rewards']}
  self.path.write_text(json.dumps(rows),encoding='utf-8')
  with self.assertRaises(ValueError):run(self.path,self.root)
 def test_modified_review_rejected(self):
  path=self.root/self.fixture.manifest[0]['review']
  value=json.loads(path.read_text(encoding='utf-8'));value['reason']='異なる採点理由に変更した試験です。'
  path.write_text(json.dumps(value),encoding='utf-8')
  with self.assertRaises(ValueError):run(self.path,self.root)
 def test_missing_original_rejected(self):
  with self.assertRaises(OSError):run(self.path,self.root/'absent')
 def test_mixed_origin_rejected(self):
  rows=json.loads(self.path.read_text(encoding='utf-8'));rows[0]['origin']='synthetic'
  self.path.write_text(json.dumps(rows),encoding='utf-8')
  with self.assertRaises(ValueError):run(self.path,self.root)
 def test_synthetic_and_exclusive_save(self):
  result=run(Path(__file__).with_name('bandit_synthetic_examples.json'),self.root/'absent')
  self.assertTrue(result['synthetic']);self.assertFalse(result['source_verified'])
  self.assertIn('人工データ',summary(result));self.assertEqual(len(result['dataset_sha256']),64)
  out=self.root/'result.json';save(out,result);original=out.read_bytes()
  with self.assertRaises(FileExistsError):save(out,result)
  self.assertEqual(original,out.read_bytes())
  with self.assertRaises(ValueError):save(self.root/'unsafe.json',dict(result,production_enabled=True))
