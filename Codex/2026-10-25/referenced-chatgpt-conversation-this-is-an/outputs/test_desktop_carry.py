from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import tomeris_plan_carry as carry
from tomeris_plans import today

class CarryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.service=carry.DesktopService(self.tmp.name,demo=True)
        self.memory=self.service.memory_path.read_bytes()
        self.service.save_plan('確認',20,[{'title':'終了した作業','minutes':5},{'title':'残った作業','minutes':10}],today())
    def tearDown(self):
        self.assertEqual(self.memory,self.service.memory_path.read_bytes())
        self.service.close(); self.tmp.cleanup()
    def bytes(self):
        return {p.name:p.read_bytes() for p in Path(self.tmp.name).glob('*.json')}
    def test_draft_excludes_completed_and_does_not_save(self):
        state=self.service.today_plan(); self.service.set_completion(state['id'],0,True)
        before=self.bytes(); draft=self.service.carry_draft(state['id'])
        self.assertEqual(draft['tasks'],[{'title':'残った作業','minutes':10}])
        self.assertEqual(draft['budget'],10)
        self.assertIn('今日の最新',draft['notice'])
        self.assertEqual(self.bytes(),before)
        draft['tasks'][0]['title']='編集した行動'
        self.service.save_plan(draft['goal'],draft['budget'],draft['tasks'],today())
        self.assertEqual(self.service.today_plan()['done'],[False])
        old=next(row for row in self.service.plan_history() if row['id']==state['id'])
        self.assertEqual(old['done'],[True,False])
        self.assertEqual(old['plan']['tasks'][1]['title'],'残った作業')
    def test_unknown_completion_is_explicit(self):
        state=self.service.today_plan(); before=self.bytes()
        draft=self.service.carry_draft(state['id'])
        self.assertEqual(len(draft['tasks']),2)
        self.assertIn('記録がないため',draft['notice'])
        self.assertEqual(self.bytes(),before)
    def test_all_done_and_missing_id_do_not_save(self):
        state=self.service.today_plan()
        self.service.set_completion(state['id'],0,True); self.service.set_completion(state['id'],1,True)
        before=self.bytes()
        for identifier in [state['id'],'missing']:
            with self.assertRaises(ValueError):
                self.service.carry_draft(identifier)
        self.assertEqual(self.bytes(),before)
    def test_old_day_draft_keeps_source_and_reads_fresh_flags(self):
        state=self.service.today_plan()
        self.service.set_completion(state['id'],1,True)
        with patch.object(carry,'today',return_value='2099-01-01'):
            draft=self.service.carry_draft(state['id'])
        self.assertEqual([t['title'] for t in draft['tasks']],['終了した作業'])
        self.assertNotIn('今日の最新',draft['notice'])
        self.assertIn(today(),draft['notice'])

if __name__=='__main__':
    unittest.main()
