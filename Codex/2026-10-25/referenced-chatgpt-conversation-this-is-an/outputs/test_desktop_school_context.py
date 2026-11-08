import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from tomeris_school_context import DesktopService

class SchoolContextTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.s.close)
 def test_location_then_principal_preserves_school(self):
  self.s.web_chat('荒川区立第一中学校はどこ？','unused',automatic=True)
  with patch.object(self.s,'report',return_value='未確認') as report:
   _,answer=self.s.prepare_context('校長は誰？')
  self.assertEqual(report.call_args.args[0],'荒川区立第一中学校 現在の校長 公式');self.assertIn('第一中学校の校長',answer)
 def test_new_school_replaces_previous(self):
  self.s.chat('荒川区立第一中学校はどこ？','unused');self.s.chat('本所高校はどこ？','unused')
  with patch.object(self.s,'report',return_value='未確認') as report:self.s.chat('校長先生はだれ？','unused')
  self.assertIn('東京都立本所高等学校',report.call_args.args[0])
 def test_clear_or_missing_context_asks_school(self):
  self.s.school_topic='以前の学校';self.s.clear_tool_context()
  with patch.object(self.s,'report',side_effect=AssertionError('search')):
   _,answer=self.s.prepare_context('校長は誰？')
  self.assertIn('どの学校',answer)
 def test_other_topic_expires_context(self):
  self.s.school_topic='以前の学校';self.s.prepare_context('こんにちは')
  self.assertIsNone(self.s.school_topic)
 def test_school_name_answers_clarification(self):
  self.s.prepare_context('校長は誰？')
  with patch.object(self.s,'report',return_value='未確認') as report:self.s.prepare_context('本所高校です')
  self.assertIn('東京都立本所高等学校 現在の校長',report.call_args.args[0])
