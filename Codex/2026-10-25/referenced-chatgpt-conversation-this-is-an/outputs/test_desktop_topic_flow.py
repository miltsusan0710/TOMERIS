import time,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from tomeris_topic_flow import DesktopService,continuation

class TopicFlowTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.s.close)
 def test_non_school_topics_and_chained_questions(self):
  for topic in ('Ollama','東京スカイツリー','電気自動車'):
   self.s.report(topic+'について調べて')
   with patch.object(self.s,'report',return_value='取得結果') as report:
    self.s.prepare_context('メリットは？');self.assertEqual(report.call_args.args[0],topic+' メリット')
    self.s.prepare_context('デメリットは？');self.assertEqual(report.call_args.args[0],topic+' デメリット')
 def test_explicit_provider_preserved(self):
  self.s.report('Ollamaについて調べて')
  with patch.object(self.s,'report',return_value='取得結果') as report:self.s.prepare_context('Googleで料金は？')
  self.assertEqual(report.call_args.args[0],'GoogleでOllama 料金 現在 公式')
 def test_new_topic_replaces_and_unrelated_expires(self):
  self.s.report('Ollamaについて調べて');self.s.report('Pythonについて調べて');self.assertEqual(self.s.flow_topic,'Python')
  self.s.prepare_context('今日の夕食を考えて');self.assertIsNone(self.s.flow_topic)
 def test_timeout_and_cancel(self):
  self.s.flow_topic='Ollama';self.s.flow_time=time.monotonic()-601
  _,answer=self.s.prepare_context('それは？');self.assertIn('対象を教えて',answer)
  self.s.report('Ollamaについて調べて');self.s.prepare_context('キャンセル');self.assertIsNone(self.s.flow_topic)
 def test_ambiguous_followup_asks_without_network(self):
  self.s.report('Ollamaについて調べて')
  with patch.object(self.s,'report',side_effect=AssertionError('search')):
   _,answer=self.s.prepare_context('それは？')
  self.assertIn('Ollama',answer);self.assertIn('どの点',answer)
 def test_explicit_subject_and_quoted_text_not_rewritten(self):
  for text in ('Pythonの料金は？','「料金は？」を英語にして','料金を調べないで'):
   self.assertIsNone(continuation(text))
 def test_normal_chat_still_uses_existing_path(self):
  self.s.chat('集中する方法を相談したい','unused')
  self.assertIsNone(self.s.flow_topic)
  with patch.object(self.s,'report',side_effect=AssertionError('search')):
   answer=self.s.chat('もっと詳しく','unused')
  self.assertIn('画面確認',answer)
 def test_local_model_receives_previous_conversation_without_search(self):
  self.s.session_turns=[('集中する方法を相談したい','通知を切る方法があります。')]
  self.s.demo=False;self.s.model_names=['test-model']
  with patch('tomeris_capabilities.LocalProvider.generate',return_value='通知を切る手順を説明します。') as generate,patch.object(self.s,'report',side_effect=AssertionError('search')):
   answer=self.s.web_chat('もっと詳しく','test-model',automatic=True)
  messages=generate.call_args.args[0]
  self.assertTrue(any(m['content']=='集中する方法を相談したい' for m in messages))
  self.assertTrue(any(m['content']=='通知を切る方法があります。' for m in messages))
  self.assertIn('手順',answer)
