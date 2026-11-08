import unittest,tempfile,time
from pathlib import Path
from unittest.mock import patch
from tomeris_topic_flow import DesktopService,topic_choices

class TopicChoicesTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.s.close)
  self.s.flow_topic='OllamaとLM Studioの比較';self.s.flow_time=time.monotonic()
 def test_asks_before_search_and_keeps_requested_method(self):
  with patch.object(self.s,'report',return_value='原文') as report:
   _,answer=self.s.prepare_context('Googleで料金は？');report.assert_not_called()
   self.assertIn('どちら',answer)
   self.s.prepare_context('LM Studio')
  self.assertEqual(report.call_args.args[0],'GoogleでLM Studio 料金 現在 公式')
 def test_cancellation_and_other_topic_clear_pending(self):
  self.s.prepare_context('料金は？');self.s.prepare_context('キャンセル');self.assertIsNone(self.s.flow_choice)
  self.s.flow_topic='AとB';self.s.flow_time=time.monotonic();self.s.prepare_context('特徴は？')
  self.s.prepare_context('こんにちは');self.assertIsNone(self.s.flow_choice)
 def test_expired_choice_does_not_search(self):
  self.s.prepare_context('料金は？');self.s.flow_choice['time']=time.monotonic()-601
  with patch.object(self.s,'report',side_effect=AssertionError('network')):_,answer=self.s.prepare_context('Ollama')
  self.assertIn('時間切れ',answer)
 def test_only_explicit_pair_split(self):
  self.assertEqual(topic_choices('OllamaとLM Studioの比較'),['Ollama','LM Studio'])
  for text in ('東京大学','AとA','AとBとC'):self.assertEqual(topic_choices(text),[])
