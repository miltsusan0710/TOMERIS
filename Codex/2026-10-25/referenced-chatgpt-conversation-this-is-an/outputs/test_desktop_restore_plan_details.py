import hashlib
import json
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from tomeris_desktop_v063 import DesktopService
from tomeris_restore_v063 import validate_rows
from tomeris_plans import today


class PlanDetailsRestoreTests(unittest.TestCase):
    def test_invalid_progress_rows(self):
        for row in (None, {}, {'done':[]}, {'done':[1]}, {'done':['false']}, {'done':[True]*4}):
            with self.assertRaises(ValueError):
                validate_rows(dict(version=1,plans={'old':row}))

    def test_invalid_reflection_rows(self):
        for row in (None, [], [None], [{}], [{'text':' '}], [{'text':123}], [{'text':'a'*2001}]):
            with self.assertRaises(ValueError):
                validate_rows(dict(version=1,plans={'old':row}), True)

    def test_old_rows_and_empty_maps_accepted(self):
        validate_rows(dict(version=1,plans={}))
        validate_rows(dict(version=1,plans={}),True)
        validate_rows(dict(version=1,plans={'old':{'done':[False,True],'extra':'keep'}}))
        validate_rows(dict(version=1,plans={'old':[{'text':'記録','extra':'keep'}]}),True)

    def test_zip_refusal_and_valid_roundtrip(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);s=DesktopService(root/'data',demo=True)
            try:
                s.save_plan('確認',10,[dict(title='読む',minutes=5)],today())
                key=s.today_plan()['id'];s.set_completion(key,0,True);s.save_reflection(key,'確認しました',0)
                archive=root/'valid.zip';s.export_backup(archive)
                info=s.inspect_backup(archive)
                folder=Path(s.restore_backup(archive,root,info['digest']))
                other=DesktopService(folder,demo=True)
                try:
                    self.assertEqual([True],other.today_plan()['done'])
                    self.assertEqual('確認しました',other.get_reflection(key)['text'])
                finally:other.close()
                before={p.name:p.read_bytes() for p in s.data_dir.glob('*.json')}
                with zipfile.ZipFile(archive) as src:contents={n:src.read(n) for n in src.namelist()}
                for name in ('plan_progress.json','plan_reflections.json'):
                    data=dict(contents);raw=json.dumps(dict(version=1,plans={key:None})).encode()
                    data[name]=raw;manifest=json.loads(data['manifest.json'])
                    for item in manifest['files']:
                        if item['name']==name:item.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
                    data['manifest.json']=json.dumps(manifest).encode()
                    bad=root/(name+'.zip')
                    with zipfile.ZipFile(bad,'w') as dst:
                        for n,v in data.items():dst.writestr(n,v)
                    folders=set(root.glob('tomeris_restored_*'))
                    with self.assertRaises(ValueError):s.inspect_backup(bad)
                    with self.assertRaises(ValueError):s.restore_backup(bad,root,hashlib.sha256(bad.read_bytes()).hexdigest())
                    self.assertEqual(folders,set(root.glob('tomeris_restored_*')))
                    self.assertEqual(before,{p.name:p.read_bytes() for p in s.data_dir.glob('*.json')})
            finally:s.close()
