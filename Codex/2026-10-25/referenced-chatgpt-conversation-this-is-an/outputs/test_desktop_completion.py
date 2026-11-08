import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import tomeris_plan_progress as progress

class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.service=progress.DesktopService(self.tmp.name,demo=True)
        self.memory=self.service.memory_path.read_bytes()
        self.service.save_plan('動作確認',10,[{'title':'確認する','minutes':5},{'title':'見返す','minutes':5}],progress.today())
        self.plan_path=Path(self.tmp.name)/'daily_plans.json'
        self.path=Path(self.tmp.name)/'plan_progress.json'
    def tearDown(self):
        self.assertEqual(self.memory,self.service.memory_path.read_bytes())
        self.service.close(); self.tmp.cleanup()
    def test_old_plan_read_without_migration_and_restart(self):
        before=self.plan_path.read_bytes()
        state=self.service.today_plan()
        self.assertEqual(state['done'],[False,False]); self.assertFalse(self.path.exists())
        self.service.set_completion(state['id'],0,True)
        self.service.close(); self.service=progress.DesktopService(self.tmp.name,demo=True)
        self.assertEqual(self.service.today_plan()['done'],[True,False])
        self.assertEqual(before,self.plan_path.read_bytes())
        self.service.set_completion(state['id'],0,False)
        self.assertEqual(self.service.today_plan()['done'],[False,False])
    def test_new_plan_is_separate_and_stale_update_rejected(self):
        old=self.service.today_plan(); self.service.set_completion(old['id'],0,True)
        self.service.save_plan('新しい計画',10,[{'title':'別の行動','minutes':5}],progress.today())
        self.assertEqual(self.service.today_plan()['done'],[False])
        with self.assertRaises(ValueError):
            self.service.set_completion(old['id'],0,False)
        self.assertEqual(json.loads(self.path.read_text(encoding='utf-8'))['plans'][old['id']]['done'],[True,False])
    def test_day_change_rejected(self):
        old=self.service.today_plan()
        with patch.object(progress,'today',return_value='2099-01-01'):
            self.assertIsNone(self.service.today_plan())
            with self.assertRaises(ValueError):
                self.service.set_completion(old['id'],0,True)
        self.assertFalse(self.path.exists())
    def test_failed_write_preserves_file(self):
        state=self.service.today_plan(); self.service.set_completion(state['id'],0,True)
        before=self.path.read_bytes()
        with patch.object(progress.os,'replace',side_effect=OSError('test')),self.assertRaises(OSError):
            self.service.set_completion(state['id'],1,True)
        self.assertEqual(before,self.path.read_bytes())
        self.assertEqual(self.service.today_plan()['done'],[True,False])
        self.assertEqual(list(Path(self.tmp.name).glob('plan_progress_*.tmp')),[])
    def test_corrupt_progress_not_overwritten(self):
        state=self.service.today_plan(); self.path.write_text('{broken',encoding='utf-8')
        with self.assertRaises(ValueError):
            self.service.set_completion(state['id'],0,True)
        self.assertEqual(self.path.read_text(),'{broken')
    def test_invalid_indices_and_types(self):
        state=self.service.today_plan()
        for index,flag in [(-1,True),(2,True),(True,True),(0,'true')]:
            with self.subTest(index=index,flag=flag),self.assertRaises(ValueError):
                self.service.set_completion(state['id'],index,flag)
        self.assertFalse(self.path.exists())

if __name__=='__main__':
    unittest.main()
