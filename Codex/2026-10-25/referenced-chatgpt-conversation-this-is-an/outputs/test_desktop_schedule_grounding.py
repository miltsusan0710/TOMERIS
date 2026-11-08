import json,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v039 import DesktopService
from tomeris_schedule_grounding import today_plan_request
from tomeris_plans import today

class ScheduleGroundingTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.s=DesktopService(Path(self.tmp.name),demo=True)
  self.addCleanup(self.tmp.cleanup);self.addCleanup(self.s.close)
 def ask(self,q='今日の予定は？'):return self.s.web_chat(q,'unused',automatic=True)
 def test_empty_never_reaches_model_or_search(self):
  with patch('tomeris_context_boundaries.DesktopService.prepare_context',side_effect=AssertionError('must intercept')):
   for ask in (self.ask,lambda q:self.s.chat(q,'unused')):
    answer=ask('今日の予定は？');self.assertIn('まだありません',answer);self.assertNotIn('朝の運動',answer)
 def test_latest_saved_plan_and_completion(self):
  for goal in ('古い計画','実際の計画'):
   self.s.save_plan(goal,10,[dict(title=goal,minutes=5)],today())
  current=self.s.today_plan();self.s.set_completion(current['id'],0,True)
  before=(self.s.data_dir/'daily_plans.json').read_bytes()
  answer=self.ask();self.assertIn('実際の計画',answer);self.assertIn('完了',answer);self.assertNotIn('古い計画',answer)
  self.assertEqual(before,(self.s.data_dir/'daily_plans.json').read_bytes())
 def test_past_plan_not_today(self):
  (self.s.data_dir/'daily_plans.json').write_text(json.dumps(dict(version=1,plans=[dict(date='2000-01-01',goal='過去',budget=5,tasks=[dict(title='昔の作業',minutes=5)])])),encoding='utf-8')
  self.assertIn('まだありません',self.ask())
 def test_corrupt_file_not_empty_and_unchanged(self):
  p=self.s.data_dir/'daily_plans.json';p.write_text('{broken',encoding='utf-8')
  self.assertIn('読み取れません',self.ask());self.assertEqual(p.read_text(),'{broken')
 def test_stale_tool_context_cleared(self):
  self.s.pending_weather='明日';self.s.pending_method='Google'
  self.ask();self.assertIsNone(self.s.pending_weather);self.assertIsNone(self.s.pending_method)
 def test_phrases_and_non_requests(self):
  for q in ('今日の予定は？','今日の予定を教えて','本日のスケジュールは何ですか','私の今日の計画を見せて'):
   self.assertTrue(today_plan_request(q),q)
  for q in ('今日の計画を作って','明日の予定は？','今日の予定は運動にする','今日の天気は？'):
   self.assertFalse(today_plan_request(q),q)
