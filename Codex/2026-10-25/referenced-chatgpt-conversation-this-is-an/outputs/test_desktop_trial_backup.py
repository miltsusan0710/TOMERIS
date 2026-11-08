import unittest,tempfile,zipfile,json
from pathlib import Path
from unittest.mock import patch
from tomeris_trial_backup import backup,inspect

class TrialBackupTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.records=self.root/'records';self.records.mkdir();self.out=self.root/'backup.zip'
  (self.records/'trial.json').write_bytes(b'{broken preserved')
  (self.records/'trial.review.1.json').write_bytes(b'{"ratings":1}')
 def test_roundtrip_preserves_even_invalid_record_and_refuses_overwrite(self):
  before={p.name:p.read_bytes() for p in self.records.iterdir()}
  manifest=backup(self.records,self.out);self.assertEqual(inspect(self.out),manifest)
  self.assertEqual(len(manifest['files']),2)
  with zipfile.ZipFile(self.out) as z:
   for name,data in before.items():self.assertEqual(z.read('records/'+name),data)
  with self.assertRaises(FileExistsError):backup(self.records,self.out)
  self.assertEqual(before,{p.name:p.read_bytes() for p in self.records.iterdir()})
 def test_internal_output_and_oversize_rejected(self):
  with self.assertRaises(ValueError):backup(self.records,self.records/'copy.zip')
  (self.records/'large.json').write_bytes(b'x'*1000001)
  with self.assertRaises(ValueError):backup(self.records,self.out)
  self.assertFalse(self.out.exists())
 def test_link_refused(self):
  with patch.object(Path,'is_symlink',return_value=True):
   with self.assertRaises(ValueError):backup(self.records,self.out)
  self.assertFalse(self.out.exists())
 def test_changed_content_detected(self):
  backup(self.records,self.out)
  with zipfile.ZipFile(self.out) as z:members={n:z.read(n) for n in z.namelist()}
  members['records/trial.json']=b'x'*len(members['records/trial.json'])
  altered=self.root/'altered.zip'
  with zipfile.ZipFile(altered,'w') as z:
   for name,data in members.items():z.writestr(name,data)
  with self.assertRaises(ValueError):inspect(altered)
 def test_extra_or_traversal_entry_rejected_without_extraction(self):
  with zipfile.ZipFile(self.out,'w') as z:
   z.writestr('manifest.json',json.dumps(dict(version=1,files=[])))
   z.writestr('../outside.json','{}')
  with self.assertRaises(ValueError):inspect(self.out)
  self.assertFalse((self.root/'outside.json').exists())
