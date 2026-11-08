import unittest,json,zipfile,hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from copy import deepcopy
from tomeris_desktop_v034 import DesktopService
from tomeris_backup_v017 import DesktopService as OldBackup
from tomeris_catalogue_schema import validate_catalogue,MAX_SOURCE_BYTES
from tomeris_restore_v034 import read_backup

ROW=dict(url='https://example.com/article',title='テスト資料',excerpt='未検証の資料です。',retrieved='2026-10-29T01:00:00+09:00')
class SourceBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.root=Path(self.temp.name)
        self.s=DesktopService(self.root/'original',demo=True);self.addCleanup(self.temp.cleanup);self.addCleanup(self.s.close)
        self.s.catalogue.save([ROW],False);self.zip=self.root/'test.zip'
    def test_roundtrip_exact_bytes_disabled_state_and_existing_data(self):
        before={p.name:p.read_bytes() for p in self.s.data_dir.glob('*.json')}
        (self.s.data_dir/'google_reports').mkdir();(self.s.data_dir/'google_reports'/'answer.html').write_text('excluded')
        (self.s.data_dir/'secret.key').write_text('excluded')
        self.s.export_backup(self.zip);info=self.s.inspect_backup(self.zip)
        self.assertEqual(info['counts']['research_sources'],1);self.assertFalse(info['counts']['source_learning_enabled'])
        destination=Path(self.s.restore_backup(self.zip,self.root,info['digest']))
        self.assertEqual((destination/'research_sources.json').read_bytes(),before['research_sources.json'])
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.s.data_dir.glob('*.json')})
        restored=DesktopService(destination,demo=True)
        try:self.assertEqual(restored.catalogue.rows,[ROW]);self.assertFalse(restored.catalogue.enabled)
        finally:restored.close()
        with zipfile.ZipFile(self.zip) as z:self.assertNotIn('secret.key',z.namelist());self.assertNotIn('google_reports/answer.html',z.namelist())
    def test_old_zip_without_sources_restores(self):
        OldBackup.export_backup(self.s,self.zip)
        info=self.s.inspect_backup(self.zip);self.assertNotIn('research_sources',info['counts'])
        folder=Path(self.s.restore_backup(self.zip,self.root,info['digest']));self.assertFalse((folder/'research_sources.json').exists())
    def test_invalid_source_on_export_keeps_original_and_no_zip(self):
        path=self.s.catalogue.path
        for raw in (b'{broken',json.dumps(dict(version=1,enabled=True,rows=[dict(ROW,url='http://127.0.0.1/')])).encode(),b' '* (MAX_SOURCE_BYTES+1)):
            path.write_bytes(raw)
            with self.assertRaises(ValueError):self.s.export_backup(self.zip)
            self.assertEqual(path.read_bytes(),raw);self.assertFalse(self.zip.exists())
    def test_rehashed_invalid_archive_refused_before_restore_folder_created(self):
        self.s.export_backup(self.zip)
        with zipfile.ZipFile(self.zip) as z:files={n:z.read(n) for n in z.namelist()}
        raw=json.dumps(dict(version=1,enabled=True,rows=[dict(ROW,retrieved='unknown')])).encode()
        files['research_sources.json']=raw;manifest=json.loads(files['manifest.json'])
        for item in manifest['files']:
            if item['name']=='research_sources.json':item.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        files['manifest.json']=json.dumps(manifest).encode()
        with zipfile.ZipFile(self.zip,'w') as z:
            for name,value in files.items():z.writestr(name,value)
        with self.assertRaises(ValueError):self.s.restore_backup(self.zip,self.root,'unused')
        self.assertFalse(list(self.root.glob('tomeris_restored_*')))
    def test_catalogue_schema_rejects_bad_urls_dates_lengths_duplicates(self):
        bad=[dict(ROW,url=u) for u in ('file:///etc/test','http://localhost/','http://192.168.1.2/','https://user:pass@example.com/','https://example.com:999/a','https://x.internal/a','https://example.com/a\nb')]
        bad += [dict(ROW,title='x'*301),dict(ROW,excerpt='x'*1201),dict(ROW,retrieved='2026-10-29'),dict(ROW,retrieved='invalid')]
        for row in bad:
            with self.subTest(row=row),self.assertRaises(ValueError):validate_catalogue(dict(version=1,enabled=True,rows=[row]))
        with self.assertRaises(ValueError):validate_catalogue(dict(version=1,enabled=True,rows=[ROW,ROW]))
    def test_zip_changed_after_inspection_preserves_data(self):
        self.s.export_backup(self.zip);info=self.s.inspect_backup(self.zip)
        with zipfile.ZipFile(self.zip,'a') as z:z.comment=b'changed'
        with self.assertRaises(ValueError):self.s.restore_backup(self.zip,self.root,info['digest'])
        self.assertFalse(list(self.root.glob('tomeris_restored_*')))
