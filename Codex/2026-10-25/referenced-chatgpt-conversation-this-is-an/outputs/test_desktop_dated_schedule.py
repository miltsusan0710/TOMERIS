import unittest,json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v040 import DesktopService
from tomeris_dated_schedule import resolve_day

class DatedScheduleTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.s=DesktopService(Path(self.tmp.name),demo=True)
  self.addCleanup(self.tmp.cleanup);self.addCleanup(self.s.close)
 def ask(self,q):return self.s.web_chat(q,'unused',automatic=True)
 def test_calendar_rollover(self):
  with patch('tomeris_dated_schedule.today',return_value='2026-12-31'):
   self.assertEqual(resolve_day('明日'),'2027-01-01');self.assertEqual(resolve_day('昨日'),'2026-12-30')
 def test_date_and_followup(self):
  with patch('tomeris_dated_schedule.today',return_value='2026-12-31'):
   self.assertIn('2026-12-31',self.ask('今日の予定は？'))
   self.assertIn('2027-01-01',self.ask('明日は？'))
   self.assertIn('2027-01-02',self.ask('明後日は？'))
 def test_latest_revision_not_other_date(self):
  plans=[dict(date=d,goal=g,budget=5,tasks=[dict(title=g,minutes=5)]) for d,g in [('2026-10-30','旧計画'),('2026-10-30','最新計画'),('2026-10-29','別日')]]
  p=self.s.data_dir/'daily_plans.json';p.write_text(json.dumps(dict(version=1,plans=plans)),encoding='utf-8');before=p.read_bytes()
  answer=self.ask('2026年10月30日の予定を教えて')
  self.assertIn('最新計画',answer);self.assertNotIn('旧計画',answer);self.assertNotIn('別日',answer)
  self.assertIn('チェック記録なし',answer);self.assertEqual(p.read_bytes(),before)
 def test_invalid_date_not_model_guess(self):
  self.assertIn('その日付は確認できません',self.ask('2026-02-30の予定は？'))
 def test_topic_switch_clears_followup(self):
  self.ask('今日の予定は？');self.ask('明日の天気は？');self.assertFalse(self.s.schedule_context)
  self.assertIn('市区町村',self.ask('明後日は？'))
 def test_broken_data_preserved(self):
  p=self.s.data_dir/'daily_plans.json';p.write_text('{oops',encoding='utf-8')
  self.assertIn('読み取れません',self.ask('明日の予定は？'));self.assertEqual(p.read_text(),'{oops')
