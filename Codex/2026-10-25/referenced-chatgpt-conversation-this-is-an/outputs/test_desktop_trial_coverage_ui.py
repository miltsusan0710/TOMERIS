import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
from tomeris_trial_coverage_ui import render,open_coverage,LABELS

class CoverageUiTests(unittest.TestCase):
 def test_render_includes_failures_and_time_distinction(self):
  report=dict(created_at='2026-11-05T00:00:00Z',total=2,counts={k:int(k in ('invalid','retrieval_failed')) for k in LABELS},
   limitation='正答率ではありません',records=[dict(file='a.json',status='retrieval_failed',finished_at='2026-11-01T00:00:00Z'),dict(file='b.json',status='invalid',error='記録不一致')])
  text=render(report)
  for required in ('試行総数：2','先頭資料の取得失敗：1','不正・読み取り不能：1','2026-11-01','記録不一致','再取得した時刻ではありません','未採点'):self.assertIn(required,text)
 def test_busy_and_closing_do_not_schedule(self):
  for busy,closing in ((True,False),(False,True)):
   app=SimpleNamespace(busy=busy,closing=closing)
   open_coverage(app)
 def test_worker_failure_and_late_close(self):
  jobs=[];app=SimpleNamespace(busy=False,closing=False,service=SimpleNamespace(data_dir=Path('unused')),submit=lambda *args:jobs.append(args))
  open_coverage(app);self.assertEqual(jobs[0][0],'plan_result')
  with patch('tomeris_trial_coverage_ui.summarize',side_effect=OSError('読めません')):
   callback,outcome=jobs[0][1]()
  self.assertEqual(outcome,(None,'読めません'));app.closing=True
  callback(outcome) # No window/root is available: late result must be ignored.
