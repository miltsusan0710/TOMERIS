from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
import tomeris_weekly as weekly

class WeeklyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.service=weekly.DesktopService(self.tmp.name,demo=True)
        self.clock=patch.object(weekly,'today',return_value='2026-10-27'); self.clock.start()
    def tearDown(self):
        self.clock.stop(); self.service.close(); self.tmp.cleanup()
    def save(self,day,tasks=1,flags=None,note=None):
        with patch('tomeris_plans.today',return_value=day),patch('tomeris_plan_progress.today',return_value=day):
            self.service.save_plan('計画 '+day,30,[{'title':f'行動 {i}','minutes':5} for i in range(tasks)],day)
            state=self.service.today_plan()
            if flags is not None:
                for i,flag in enumerate(flags): self.service.set_completion(state['id'],i,flag)
            if note: self.service.save_reflection(state['id'],note,0)
    def test_empty_seven_days_no_files(self):
        report=self.service.weekly_report()
        self.assertEqual((report['start'],report['end']),('2026-10-21','2026-10-27'))
        self.assertEqual(len(report['days']),7); self.assertEqual(report['planned_days'],0)
        self.assertEqual(weekly.format_report(report).count('計画の保存なし'),7)
        self.assertFalse((Path(self.tmp.name)/'daily_plans.json').exists())
    def test_boundaries_latest_only_and_unknown(self):
        self.save('2026-10-20',flags=[True]); self.save('2026-10-28',flags=[True])
        self.save('2026-10-21')
        self.save('2026-10-25',flags=[True],note='以前の振り返り')
        self.save('2026-10-25')
        self.save('2026-10-27',tasks=2,flags=[True,False],note='今日の原文\n次はゆっくり。')
        before={p.name:p.read_bytes() for p in Path(self.tmp.name).glob('*.json')}
        report=self.service.weekly_report()
        self.assertEqual([report[k] for k in ['planned_days','completed','unchecked','unknown','planned_minutes','reflection_days']],[3,1,1,2,20,1])
        text=weekly.format_report(report)
        self.assertIn('今日の原文\n次はゆっくり。',text)
        self.assertNotIn('以前の振り返り',text)
        self.assertNotIn('2026-10-20',text); self.assertNotIn('2026-10-28',text)
        self.assertEqual(before,{p.name:p.read_bytes() for p in Path(self.tmp.name).glob('*.json')})
    def test_year_boundary(self):
        with patch.object(weekly,'today',return_value='2027-01-02'):
            report=self.service.weekly_report()
        self.assertEqual(report['start'],'2026-12-27')
        self.assertEqual(report['days'][-1]['date'],'2027-01-02')
    def test_corrupt_file_preserved(self):
        path=Path(self.tmp.name)/'plan_reflections.json'; path.write_text('{broken')
        with self.assertRaises(ValueError): self.service.weekly_report()
        self.assertEqual(path.read_text(),'{broken')

if __name__=='__main__': unittest.main()
