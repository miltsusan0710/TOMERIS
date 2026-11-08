import unittest,tempfile,json,zipfile,io
from pathlib import Path
from tomeris_learning_backup import create,inspect,restore,inspect_bytes
from tomeris_learning_review import ReviewCatalogue
from tomeris_source_catalogue import Catalogue

class LearningBackupTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.data=self.root/'data';self.data.mkdir();self.archive=self.root/'data.zip'
  self.raw=json.dumps(dict(version=1,attempts=[dict(action='exact',success=False,outcome='retrieval_error')])).encode()
  (self.data/'retrieval_experience.json').write_bytes(self.raw)
 def test_roundtrip_and_exclusive_target(self):
  gate=ReviewCatalogue(Catalogue(self.data),self.data/'learning_review.json')
  text='暴力を推奨するという文章です。'
  gate.learn([dict(page=dict(title='確認',url='https://example.org/a',text=text),excerpts=[text])])
  create(self.data,self.archive);checked=inspect(self.archive)
  restore(self.archive,self.root,checked['digest'])
  folder=next(self.root.glob('tomeris_learning_restored_*'))
  self.assertEqual((folder/'retrieval_experience.json').read_bytes(),self.raw)
  self.assertEqual((folder/'learning_review.json').read_bytes(),(self.data/'learning_review.json').read_bytes())
  with self.assertRaises(FileExistsError):create(self.data,self.archive)
 def test_changed_zip_does_not_create_folder(self):
  create(self.data,self.archive)
  with self.assertRaises(ValueError):restore(self.archive,self.root,'wrong digest')
  self.assertEqual(list(self.root.glob('tomeris_learning_restored_*')),[])
 def test_invalid_outcome_refused_without_target(self):
  (self.data/'retrieval_experience.json').write_text(json.dumps(dict(version=1,attempts=[dict(action='exact',success=True,outcome='retrieval_error')])))
  with self.assertRaises(ValueError):create(self.data,self.archive)
  self.assertFalse(self.archive.exists())
 def test_unexpected_member_rejected(self):
  data=io.BytesIO()
  with zipfile.ZipFile(data,'w') as z:z.writestr('../escape.json','{}');z.writestr('manifest.json','{}')
  with self.assertRaises(ValueError):inspect_bytes(data.getvalue())
