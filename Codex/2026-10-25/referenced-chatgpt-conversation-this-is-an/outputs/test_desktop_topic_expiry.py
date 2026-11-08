import unittest,tempfile,time
from pathlib import Path
from unittest.mock import patch
from tomeris_topic_flow import DesktopService

class TopicExpiryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.s.close)
  self.s.flow_topic='以前の製品';self.s.flow_time=time.monotonic()-601
  self.s.last_research_request='以前の製品について調べて'
  self.s.school_topic='以前の学校'
 def test_expired_detail_cannot_revive_older_research(self):
  with patch.object(self.s,'report',side_effect=AssertionError('must not search')):
   answer=self.s.web_chat('もっと詳しく','unused',automatic=True)
  self.assertIn('対象を確認',answer)
  self.assertIsNone(self.s.last_research_request);self.assertIsNone(self.s.flow_topic);self.assertIsNone(self.s.school_topic)
 def test_expired_price_asks_before_transmitting(self):
  with patch.object(self.s,'report',side_effect=AssertionError('must not search')):
   _,answer=self.s.prepare_context('Googleで料金は？')
  self.assertIn('対象名',answer);self.assertIsNone(self.s.last_research_request)
 def test_active_followup_still_routes(self):
  self.s.flow_time=time.monotonic()
  with patch.object(self.s,'report',return_value='原文') as report:
   _,answer=self.s.prepare_context('料金は？')
  self.assertEqual(report.call_args.args[0],'以前の製品 料金 現在 公式')
  self.assertIn('前の話題',answer)
