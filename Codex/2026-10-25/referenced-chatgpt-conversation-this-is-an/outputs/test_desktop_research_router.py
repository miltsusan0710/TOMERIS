import tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from tomeris_research_router import DesktopService, BaseService
from tomeris_research_intent import research_intent

class ResearchRouterTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.s.close)
 def test_information_paraphrases_route_before_model(self):
  for question in ('東海大学について知りたい','東京大学について知りたい','光合成について教えて',
                   'マリー・キュリーについて説明して','量子力学とは何ですか？','Ollamaって何？',
                   '私立大学について知りたい','人間の記憶について知りたい'):
   with self.subTest(question=question),patch.object(self.s,'report',return_value='本文と出典') as report:
    self.assertEqual(self.s.chat(question,'unused'),'本文と出典');report.assert_called_once()
   with patch.object(self.s,'report',return_value='本文と出典') as report:
    self.assertEqual(self.s.web_chat(question,'unused',automatic=True),'本文と出典');report.assert_called_once()
 def test_conversation_personal_and_quoted_requests_stay_local(self):
  for q in ('疲れたので励まして','こんにちは','今日の作業の相談に乗って','私の目標について教えて','「東海大学について知りたい」を英訳して'):
   self.assertIsNone(research_intent(q),q)
 def test_provider_and_current_attributes(self):
  self.assertEqual(research_intent('Googleで東海大学について知りたい')['query'],'Googleで東海大学について調べて')
  self.assertEqual(research_intent('東海大学の学費はいくら？')['query'],'東海大学 学費 現在 公式')
 def test_pronoun_requires_context_and_expiry(self):
  with patch.object(self.s,'report') as report:
   self.assertIn('対象名',self.s.chat('それについて知りたい','unused'));report.assert_not_called()
  self.s.flow_topic='光合成';self.s.flow_time=time.monotonic()
  with patch.object(self.s,'report',return_value='原文') as report:
   self.s.chat('それについて知りたい','unused');self.assertEqual(report.call_args.args[0],'光合成について調べて')
  self.s.flow_time-=601
  with patch.object(self.s,'report') as report:
   self.s.chat('それについて知りたい','unused');report.assert_not_called()
 def test_no_evidence_retries_once_without_model(self):
  self.s.demo=False;self.s.last_evidence_items=[]
  with patch.object(BaseService,'report',return_value='根拠なし') as report:
   answer=self.s.report('東海大学について知りたい')
  self.assertEqual([c.args[0] for c in report.call_args_list],['東海大学について調べて','東海大学 公式'])
  self.assertIn('補っていません',answer);self.assertEqual(self.s.flow_topic,'東海大学')
 def test_success_and_explicit_provider_do_not_retry(self):
  self.s.demo=False;self.s.last_evidence_items=[{'page':{}}]
  with patch.object(BaseService,'report',return_value='原文') as report:
   self.s.report('光合成について知りたい');self.assertEqual(report.call_count,1)
  self.s.last_evidence_items=[]
  with patch.object(BaseService,'report',return_value='指定方法の結果') as report:
   self.s.report('Wikipediaで光合成について知りたい');self.assertEqual(report.call_count,1)
