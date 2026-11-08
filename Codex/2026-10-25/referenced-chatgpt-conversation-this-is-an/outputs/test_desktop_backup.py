import hashlib,json,zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
import tomeris_backup as backup
from tomeris_plans import today

class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.service=backup.DesktopService(self.root/'data',demo=True)
        self.target=self.root/'backup.zip'
    def tearDown(self):
        self.service.close(); self.tmp.cleanup()
    def test_complete_archive_exact_bytes_and_secrets_excluded(self):
        self.service.save_plan('バックアップ確認',10,[{'title':'試す','minutes':5}],today())
        state=self.service.today_plan(); self.service.set_completion(state['id'],0,True)
        self.service.save_reflection(state['id'],'確認できた',0)
        (self.service.data_dir/'google_connection.dpapi').write_bytes(b'fake-google-secret')
        (self.service.data_dir/'credentials.json').write_bytes(b'fake-oauth-secret')
        before={p.name:p.read_bytes() for p in self.service.data_dir.iterdir() if p.is_file() and p.name!='session.lock'}
        self.service.export_backup(self.target)
        with zipfile.ZipFile(self.target) as archive:
            self.assertEqual(set(archive.namelist()),set(backup.FILES)|{'manifest.json','README.txt'})
            manifest=json.loads(archive.read('manifest.json'))
            self.assertEqual(len(manifest['files']),4)
            for item in manifest['files']:
                raw=archive.read(item['name']); self.assertEqual(raw,before[item['name']])
                self.assertEqual(hashlib.sha256(raw).hexdigest(),item['sha256'])
                self.assertEqual(len(raw),item['bytes'])
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.service.data_dir.iterdir() if p.is_file() and p.name!='session.lock'})
    def test_memory_only_and_missing_optional_files(self):
        self.service.export_backup(self.target)
        with zipfile.ZipFile(self.target) as archive:
            manifest=json.loads(archive.read('manifest.json'))
            self.assertEqual(set(manifest['not_created']),set(backup.FILES)-{'tomeris_memory.json'})
    def test_never_overwrites_existing_destination(self):
        self.target.write_bytes(b'existing backup')
        with self.assertRaises(ValueError): self.service.export_backup(self.target)
        self.assertEqual(self.target.read_bytes(),b'existing backup')
    def test_write_failure_removes_only_new_archive(self):
        with patch.object(backup.zipfile.ZipFile,'writestr',side_effect=OSError('test')),self.assertRaises(OSError):
            self.service.export_backup(self.target)
        self.assertFalse(self.target.exists())
        self.assertTrue(self.service.memory_path.exists())
    def test_verification_failure_removes_failed_archive(self):
        with patch.object(backup.zipfile.ZipFile,'testzip',return_value='bad'),self.assertRaises(OSError):
            self.service.export_backup(self.target)
        self.assertFalse(self.target.exists())
    def test_corrupt_source_or_limit_does_not_create_zip(self):
        with patch.object(backup,'MAX_FILE_BYTES',1),self.assertRaises(ValueError):
            self.service.export_backup(self.target)
        self.assertFalse(self.target.exists())
        path=self.service.data_dir/'daily_plans.json'; path.write_text('{broken')
        with self.assertRaises(ValueError): self.service.export_backup(self.target)
        self.assertFalse(self.target.exists()); self.assertEqual(path.read_text(),'{broken')

if __name__=='__main__': unittest.main()
