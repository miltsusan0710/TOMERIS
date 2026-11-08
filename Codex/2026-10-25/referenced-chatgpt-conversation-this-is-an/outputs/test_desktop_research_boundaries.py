import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v049 import DesktopService
GOOD='Ollamaはローカル環境でモデルを実行するためのツールとして説明されています。'
class ResearchBoundaryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.s.close)
 def ask(self,q):return self.s.web_chat(q,'unused',automatic=True)
 def research(self,q,url):
  self.s.demo=False;row=dict(title='Ollama',url=url,snippet=GOOD)
  with patch.object(self.s.methods,'candidates',return_value=([row],[])),patch('tomeris_evidence_v029.fetch_page',return_value=dict(row,text=GOOD,published='')):
   return self.ask(q)
 def test_successful_followup_keeps_target_new_source(self):
  self.research('Ollamaについて調べて','https://example.com/first')
  answer=self.research('他の情報は？','https://example.com/second')
  self.assertIn('追加調査：Ollama',answer);self.assertIn('https://example.com/second',answer)
  self.assertNotIn('https://example.com/first',answer)
  self.assertIn('https://example.com/second',self.ask('その出典は？'))
 def test_failed_followup_clears_old_source_and_target(self):
  self.research('Ollamaについて調べて','https://example.com/first')
  with patch.object(self.s.methods,'candidates',return_value=([],[])):self.ask('他の情報は？')
  self.assertIsNone(self.s.last_research_request)
  self.assertIn('出典は確認できません',self.ask('その出典は？'))
  with patch.object(self.s.methods,'candidates',side_effect=AssertionError('no stale research')):
   self.assertIn('対象を教えて',self.ask('他の情報は？'))
 def test_topic_reset_prevents_old_followup(self):
  self.research('Ollamaについて調べて','https://example.com/first')
  self.assertIn('話題を切り替えました',self.ask('別の話'))
  self.assertIsNone(self.s.last_research_request);self.assertIsNone(self.s.research_source_snapshot)
  self.assertIn('対象を教えて',self.ask('他の情報は？'))
 def test_prefix_routes_new_question(self):
  self.s.pending_method='Google';self.s.pending_weather='明日'
  self.assertIn('結果：12',self.ask('別の話、計算: 3*4'))
  self.assertIsNone(self.s.pending_method);self.assertIsNone(self.s.pending_weather)
 def test_no_subject_no_model_invention(self):
  self.assertIn('対象を教えて',self.ask('他の情報は？'))
