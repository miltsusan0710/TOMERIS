import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v067 import DesktopService
from tomeris_search_methods import MethodError
from test_desktop_overview import INTRO,DETAIL

class DetailFollowupTests(unittest.TestCase):
 def setUp(self):
  tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup)
  self.s=DesktopService(Path(tmp.name),demo=True);self.addCleanup(self.s.close);self.s.demo=False
  self.row=dict(title='トニー・スターク',url='https://ja.wikipedia.org/wiki/tony',snippet=INTRO,wiki_id=2)
  self.page=dict(title=self.row['title'],url=self.row['url'],text=INTRO+'\n== 別作品 ==\n'+DETAIL,published='',provider='Wikipedia（二次資料）')
  self.c=patch('tomeris_research_learning.BaseMethods.candidates',return_value=([self.row],[]));self.c.start();self.addCleanup(self.c.stop)
 def ask(self,text):return self.s.web_chat(text,'unused',automatic=True)
 def test_refetch_details_not_lead_and_other_sources_remain_excluded(self):
  with patch('tomeris_evidence_v029.wikipedia_page',return_value=self.page) as fetch:
   first=self.ask('トニースタークについて調べて');self.assertNotIn(DETAIL,first)
   answer=self.ask('もっと詳しく');self.assertIn(DETAIL,answer);self.assertNotIn(INTRO,answer);self.assertEqual(fetch.call_count,2)
   self.ask('他の情報は？');self.assertEqual(fetch.call_count,2)
  self.assertIsNone(self.s._detail_subject)
 def test_failed_refetch_does_not_return_old_text(self):
  with patch('tomeris_evidence_v029.wikipedia_page',return_value=self.page):self.ask('トニースタークについて調べて')
  with patch('tomeris_evidence_v029.wikipedia_page',side_effect=MethodError('offline')):
   answer=self.ask('もっと詳しく');self.assertIn('本文根拠を取得できません',answer);self.assertNotIn(INTRO,answer);self.assertNotIn(DETAIL,answer)
  self.assertIn(self.row['url'],self.s.followup_seen_urls)
 def test_without_overview_uses_existing_clarification(self):
  self.assertIn('対象を教えて',self.ask('もっと詳しく'))
 def test_method_override_forwarded_and_flag_cleared_on_exception(self):
  self.s.last_research_request='トニースタークについて調べて'
  with patch.object(self.s,'report',side_effect=RuntimeError('failed')) as report:
   with self.assertRaises(RuntimeError):self.s.continue_research('Wikipedia英語で詳しく')
   self.assertEqual(report.call_args.args[0],'Wikipedia英語でトニースタークについて調べて')
  self.assertFalse(self.s._continuing);self.assertIsNone(self.s._detail_subject)
 def test_no_section_does_not_repeat_intro(self):
  self.page['text']=INTRO
  with patch('tomeris_evidence_v029.wikipedia_page',return_value=self.page):
   self.ask('トニースタークについて調べて');answer=self.ask('もっと詳しく')
  self.assertNotIn(INTRO,answer);self.assertIn('本文根拠を取得できません',answer)
