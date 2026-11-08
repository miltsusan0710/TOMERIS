import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import tomeris_plan_history as history
from tomeris_plans import today

class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.service=history.DesktopService(self.tmp.name,demo=True)
        self.before=self.service.memory_path.read_bytes()
    def tearDown(self):
        self.assertEqual(self.before,self.service.memory_path.read_bytes())
        self.service.close(); self.tmp.cleanup()
    def save(self,goal='計画'):
        self.service.save_plan(goal,10,[{'title':'確認する','minutes':5}],today())
    def test_empty_no_files_created(self):
        self.assertEqual(self.service.plan_history(),[])
        self.assertFalse((Path(self.tmp.name)/'plan_progress.json').exists())
        self.assertFalse((Path(self.tmp.name)/'daily_plans.json').exists())
    def test_revisions_completion_and_no_writes(self):
        self.save('最初'); old=self.service.today_plan()
        self.service.set_completion(old['id'],0,True)
        self.save('次')
        paths=[Path(self.tmp.name)/name for name in ['daily_plans.json','plan_progress.json']]
        before=[p.read_bytes() for p in paths]
        rows=self.service.plan_history()
        self.assertEqual([r['revision'] for r in rows],[2,1])
        self.assertTrue(rows[0]['latest']); self.assertFalse(rows[1]['latest'])
        self.assertFalse(rows[0]['recorded']); self.assertTrue(rows[1]['recorded'])
        self.assertEqual(rows[1]['id'],old['id']); self.assertEqual(rows[1]['done'],[True])
        self.assertIn('チェック記録なし',history.describe(rows[0]))
        self.assertIn('［完了］',history.describe(rows[1]))
        self.assertEqual([p.read_bytes() for p in paths],before)
        rows[1]['plan']['goal']='changed'
        self.assertEqual(self.service.plan_history()[1]['plan']['goal'],'最初')
    def test_multiple_dates_newest_first_and_full_text(self):
        with patch('tomeris_plans.today',return_value='2026-10-25'):
            self.service.save_plan('以前の計画',10,[{'title':'読む','minutes':5}],'2026-10-25')
        self.save('長い目標'*100)
        rows=self.service.plan_history()
        self.assertEqual(rows[0]['plan']['date'],today())
        self.assertTrue(all(r['latest'] for r in rows))
        self.assertIn('長い目標'*100,history.describe(rows[0]))
    def test_corrupt_completion_preserved(self):
        self.save(); path=Path(self.tmp.name)/'plan_progress.json'; path.write_text('{broken')
        with self.assertRaises(ValueError):
            self.service.plan_history()
        self.assertEqual(path.read_text(),'{broken')
    def test_mismatched_flags_rejected(self):
        self.save(); state=self.service.today_plan()
        path=Path(self.tmp.name)/'plan_progress.json'
        path.write_text(json.dumps({'version':1,'plans':{state['id']:{'done':[True,False]}}}))
        with self.assertRaises(ValueError):
            self.service.plan_history()

if __name__=='__main__':
    unittest.main()
