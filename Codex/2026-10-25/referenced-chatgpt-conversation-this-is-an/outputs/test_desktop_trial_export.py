import json,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from tomeris_research_trials import save_record,save_review
from tomeris_trial_export import dataset,export
from tomeris_bandit_lab import experiment

class ExportTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.manifest=[]
  for i,(split,context) in enumerate([('train','overview'),('train','specific'),('test','overview'),('test','specific')]):
   url=f'https://example.org/{i}';text=f'対象{i}の説明文を含む実装試験用の人工資料です。'
   record=dict(version=1,id=f'{i:032x}',query=f'対象{i}',context=context,finished_at='2026-11-05T00:00:00+00:00',candidates=[dict(url=url)],rankings={a:[url] for a in ('search_order','exact_title_first')},pages=[dict(url=url,status='retrieved',page=dict(text=text),excerpts=[text])])
   path=save_record(self.root,record);review=save_review(path,dict(search_order=1,exact_title_first=1),'試験用の採点です。実データとして使用しません。')
   self.manifest.append(dict(record=path.name,review=review.name,topic_id=f'group{i}',split=split))
 def test_roundtrip_exclusive_and_no_training_side_effect(self):
  out=self.root/'dataset.json';self.assertEqual(export(self.root,self.manifest,out),4)
  rows=json.loads(out.read_text(encoding='utf-8'));self.assertEqual(len(rows[0]['provenance']['record_sha256']),64)
  self.assertFalse(experiment(rows)['production_enabled'])
  with self.assertRaises(FileExistsError):export(self.root,self.manifest,out)
 def test_leakage_and_duplicate_reviews(self):
  self.manifest[2]['topic_id']='GROUP0'
  with self.assertRaises(ValueError):dataset(self.root,self.manifest)
  self.manifest[2]=dict(self.manifest[0],split='test',topic_id='other')
  with self.assertRaises(ValueError):dataset(self.root,self.manifest)
 def test_wrong_review_binding(self):
  self.manifest[0]['review']=self.manifest[1]['review']
  with self.assertRaises(ValueError):dataset(self.root,self.manifest)
 def test_path_escape_and_unrated(self):
  path=self.manifest[0]['record'];self.manifest[0]['record']='../'+path
  with self.assertRaises(ValueError):dataset(self.root,self.manifest)
  self.manifest[0]['record']=path
  review=self.root/self.manifest[0]['review'];data=json.loads(review.read_text(encoding='utf-8'));data['ratings']['search_order']=None;review.write_text(json.dumps(data),encoding='utf-8')
  with self.assertRaises(ValueError):dataset(self.root,self.manifest)
 def test_mismatched_same_document_ratings(self):
  review=self.root/self.manifest[0]['review'];data=json.loads(review.read_text(encoding='utf-8'));data['ratings']['search_order']=-1;review.write_text(json.dumps(data),encoding='utf-8')
  with self.assertRaises(ValueError):dataset(self.root,self.manifest)
 def test_missing_or_unmatched_evidence_even_with_new_hash(self):
  from tomeris_research_trials import digest
  path=self.root/self.manifest[0]['record'];envelope=json.loads(path.read_text(encoding='utf-8'));envelope['record']['pages'][0]['excerpts']=['本文にはない文章'];envelope['sha256']=digest(envelope['record']);path.write_text(json.dumps(envelope),encoding='utf-8')
  review=self.root/self.manifest[0]['review'];data=json.loads(review.read_text(encoding='utf-8'));data['record_sha256']=envelope['sha256'];review.write_text(json.dumps(data),encoding='utf-8')
  with self.assertRaises(ValueError):dataset(self.root,self.manifest)
