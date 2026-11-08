import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v037 import DesktopService
from test_desktop_research_continuation import ROWS,page
from test_desktop_earthquake_followup import get
import tomeris_search_methods as providers
import tomeris_evidence_v029 as evidence
import tomeris_earthquake_followup as quake

class ContextBoundaryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.tmp.cleanup);self.addCleanup(self.s.close)
 def ask(self,text):return self.s.web_chat(text,'none',automatic=True)
 def test_pending_google_does_not_capture_calculation(self):
  self.ask('Googleで調べて');self.assertEqual(self.s.pending_method,'Google')
  with patch('tomeris_auto_research_v029.webbrowser.open') as browser:
   self.assertIn('結果：4',self.ask('計算: 2+2'));browser.assert_not_called()
  self.assertIsNone(self.s.pending_method)
 def test_pending_google_does_not_capture_weather(self):
  self.ask('Googleで調べて');self.ask('明後日の天気は？')
  self.assertIsNone(self.s.pending_method);self.assertEqual(self.s.pending_weather,'明後日')
  self.assertIn('荒川区の明後日',self.ask('荒川区'))
 def test_new_placeless_weather_does_not_reuse_previous_city(self):
  self.ask('荒川区の明日の天気');self.ask('明日の天気は？')
  self.assertIsNone(self.s.last_weather_place)
  with patch('tomeris_weather_service.fetch_weather') as fetch:
   self.assertIn('市区町村',self.ask('明後日は？'));fetch.assert_not_called()
  self.assertIn('平塚市の明後日',self.ask('平塚市'))
 def test_preferences_and_learning_menu_clear_weather_context(self):
  for command in ('今後は回答を短くして','学習した資料を見せて'):
   self.ask('荒川区の明日の天気');self.ask(command);self.assertIsNone(self.s.pending_weather);self.assertIsNone(self.s.last_weather_place)
  self.ask('荒川区の明日の天気');self.s.special('ネット学習を停止');self.assertIsNone(self.s.pending_weather)
 def test_cancel_all_tool_context_from_normal_weather(self):
  self.ask('明後日の天気は？');answer=self.ask('キャンセル')
  self.assertIn('取り消しました',answer);self.assertIsNone(self.s.pending_weather);self.assertIsNone(self.s.pending_method)
 def test_explicit_topic_switch_forgets_tool_and_local_turns(self):
  self.ask('Googleで調べて');answer=self.ask('話題を変えて、計算: 3+4')
  self.assertIn('結果：7',answer);self.assertIsNone(self.s.pending_method)
  self.assertFalse(any('Google' in q for q,a in self.s.session_turns))
 def test_weather_more_information_is_not_old_research(self):
  self.s.last_research_request='アイアンマン';self.ask('荒川区の明日の天気')
  answer=self.ask('他の情報は？');self.assertIn('天気のどの情報',answer);self.assertNotIn('アイアンマン',answer)
 def test_explicit_provider_followup_retains_research_and_excludes_seen(self):
  self.s.demo=False
  with patch.object(providers,'wikipedia_search',return_value=ROWS),patch.object(evidence,'wikipedia_page',side_effect=page):
   self.ask('Wikipediaでアイアンマンについて調べて')
   answer=self.ask('Wikipediaで他の情報は？');self.assertIn('資料3',answer);self.assertNotIn('資料1',answer)
 def test_quake_more_information_targets_same_event(self):
  self.s.demo=False;first=get(minute='08');second=get(first,place='同じ地震')
  with patch.object(quake,'snapshot',side_effect=[first,second]) as fetch:
   self.ask('今の地震の震源は？');answer=self.ask('もっと詳しく');self.assertIn('同じ地震',answer);self.assertEqual(fetch.call_args.args[0]['event_id'],first['event_id'])
