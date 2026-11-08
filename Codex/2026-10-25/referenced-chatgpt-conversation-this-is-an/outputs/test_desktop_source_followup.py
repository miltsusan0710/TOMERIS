import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v042 import DesktopService

GOOD='Ollamaはローカル環境でモデルを実行するためのツールとして説明されています。'
class SourceFollowupTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.tmp.cleanup);self.addCleanup(self.s.close)
 def research(self,success=True):
  self.s.demo=False
  row=dict(title='Ollamaの説明',url='https://example.com/ollama',snippet=GOOD)
  with patch.object(self.s.methods,'candidates',return_value=([row],[])),patch('tomeris_evidence_v029.fetch_page',return_value=dict(row,text=GOOD if success else '関係のない本文',published='')):
   return self.s.web_chat('Ollamaについて調べて','unused',automatic=True)
 def ask(self,q='その出典は？'):return self.s.web_chat(q,'unused',automatic=True)
 def test_real_report_path_and_followup_no_network(self):
  self.research()
  with patch.object(self.s.methods,'candidates',side_effect=AssertionError('unexpected search')):
   answer=self.ask();self.assertIn('https://example.com/ollama',answer);self.assertIn('今回は再取得していません',answer)
   self.assertIn('Ollama',answer);self.assertIn('取得時刻',answer)
   self.assertEqual(answer,self.ask('情報源を教えて'))
 def test_no_prior_sources_no_guess(self):
  self.assertIn('出典は確認できません',self.ask())
 def test_failed_research_drops_old_sources(self):
  self.research();self.research(False);self.assertIn('出典は確認できません',self.ask())
 def test_topic_change_clears_sources(self):
  self.research();self.s.demo=True;self.ask('今日の予定は？')
  self.assertIn('出典は確認できません',self.ask())
 def test_cancel_clears_sources(self):
  self.research();self.ask('キャンセル');self.assertIn('出典は確認できません',self.ask())
 def test_normal_chat_path(self):
  self.research();answer=self.s.chat('その出典は？','unused')
  self.assertIn('https://example.com/ollama',answer)
