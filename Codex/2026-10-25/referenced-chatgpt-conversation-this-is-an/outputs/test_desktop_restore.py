import hashlib,json,zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
import tomeris_restore as restore
from tomeris_plans import today

class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.service=restore.DesktopService(self.root/'original',demo=True)
        self.service.save_plan('復元確認',10,[{'title':'記録を見る','minutes':5}],today())
        state=self.service.today_plan(); self.service.set_completion(state['id'],0,True)
        self.service.save_reflection(state['id'],'復元して確認する。',0)
        self.backup=self.root/'backup.zip'; self.service.export_backup(self.backup)
        self.before={p.name:p.read_bytes() for p in self.service.data_dir.glob('*.json')}
    def tearDown(self):
        self.assertEqual(self.before,{p.name:p.read_bytes() for p in self.service.data_dir.glob('*.json')})
        self.service.close(); self.tmp.cleanup()
    def rewrite(self,mutate):
        with zipfile.ZipFile(self.backup) as archive: data={name:archive.read(name) for name in archive.namelist()}
        mutate(data)
        with zipfile.ZipFile(self.backup,'w',zipfile.ZIP_DEFLATED) as archive:
            for name,raw in data.items(): archive.writestr(name,raw)
    def test_roundtrip_new_folder_exact_data_and_load(self):
        check=self.service.inspect_backup(self.backup)
        self.assertEqual(check['counts']['plans'],1)
        self.assertNotIn('payload',check)
        folder=Path(self.service.restore_backup(self.backup,self.root,check['digest']))
        self.assertNotEqual(folder,self.service.data_dir)
        self.assertEqual(self.before,{p.name:p.read_bytes() for p in folder.iterdir()})
        other=restore.DesktopService(folder,demo=True)
        try:
            self.assertEqual(other.today_plan()['done'],[True])
            self.assertEqual(other.plan_history()[0]['reflection'],'復元して確認する。')
        finally: other.close()
        second=Path(self.service.restore_backup(self.backup,self.root,check['digest']))
        self.assertNotEqual(folder,second)
    def test_preview_no_write(self):
        before={p.name for p in self.root.iterdir()}
        self.service.inspect_backup(self.backup)
        self.assertEqual(before,{p.name for p in self.root.iterdir()})
    def test_hash_mismatch_and_zip_changed_after_preview(self):
        check=self.service.inspect_backup(self.backup)
        self.rewrite(lambda data:data.update({'README.txt':b'changed documentation'}))
        with self.assertRaises(ValueError): self.service.restore_backup(self.backup,self.root,check['digest'])
        self.assertEqual(list(self.root.glob('tomeris_restored_*')),[])
        self.rewrite(lambda data:data.update({'tomeris_memory.json':b'{}'}))
        with self.assertRaises(ValueError): self.service.inspect_backup(self.backup)
    def test_path_traversal_and_extra_file_rejected(self):
        self.rewrite(lambda data:data.update({'../escape.json':b'{}'}))
        with self.assertRaises(ValueError): self.service.inspect_backup(self.backup)
        self.assertFalse((self.root/'escape.json').exists())
    def test_duplicate_name_rejected(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            with zipfile.ZipFile(self.backup,'a') as archive: archive.writestr('README.txt','duplicate')
        with self.assertRaises(ValueError): self.service.inspect_backup(self.backup)
    def test_symlink_and_size_limit_rejected(self):
        with patch.object(restore,'MAX_FILE_BYTES',1),self.assertRaises(ValueError): self.service.inspect_backup(self.backup)
        with zipfile.ZipFile(self.backup) as archive: data={name:archive.read(name) for name in archive.namelist()}
        with zipfile.ZipFile(self.backup,'w') as archive:
            for name,raw in data.items():
                if name=='tomeris_memory.json':
                    info=zipfile.ZipInfo(name); info.create_system=3; info.external_attr=(0o120777<<16)
                    archive.writestr(info,raw)
                else: archive.writestr(name,raw)
        with self.assertRaises(ValueError): self.service.inspect_backup(self.backup)
    def test_missing_manifest_or_invalid_zip(self):
        self.rewrite(lambda data:data.pop('manifest.json'))
        with self.assertRaises(ValueError): self.service.inspect_backup(self.backup)
        self.backup.write_bytes(b'not a zip')
        with self.assertRaises(ValueError): self.service.inspect_backup(self.backup)
    def test_write_failure_does_not_touch_original(self):
        check=self.service.inspect_backup(self.backup)
        original_open=Path.open
        def fail(path,*args,**kwargs):
            if path.name=='plan_progress.json' and path.parent.name.startswith('tomeris_restored_') and args and args[0]=='xb':
                raise OSError('test failure')
            return original_open(path,*args,**kwargs)
        with patch.object(Path,'open',fail),self.assertRaises(OSError):
            self.service.restore_backup(self.backup,self.root,check['digest'])
        self.assertEqual(list(self.root.glob('tomeris_restored_*')),[])

if __name__=='__main__': unittest.main()
