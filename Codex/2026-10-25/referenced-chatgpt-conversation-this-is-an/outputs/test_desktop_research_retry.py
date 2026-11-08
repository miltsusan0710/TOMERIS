import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v044 import DesktopService
GOOD='Ollamaはローカル環境でモデルを実行するためのツールとして説明されています。'
class ResearchRetryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.s.close)
  self.r=self.s.research_journal.append('Ollamaについて調べて','選択設定：自動（実際の提供元は出典を参照）',[dict(title='旧資料',url='https://example.com/old')])
 def ask(self,q):return self.s.web_chat(q,'unused',automatic=True)
 def review(self):
  self.ask('/research-retry '+self.r['id']);return self.s.retry_review['token']
 def test_review_no_network_then_new_fetch(self):
  with patch.object(self.s.methods,'candidates',side_effect=AssertionError('no search')):
   token=self.review()
  self.s.demo=False;row=dict(title='新資料',url='https://example.com/new',snippet=GOOD)
  with patch.object(self.s.methods,'candidates',return_value=([row],[])),patch('tomeris_evidence_v029.fetch_page',return_value=dict(row,text=GOOD,published='')) as fetch:
   answer=self.ask('/research-confirm '+token);fetch.assert_called_once()
  self.assertIn('https://example.com/new',answer);self.assertNotIn('https://example.com/old',answer)
  self.assertEqual(len(self.s.research_journal.read()),2)
  self.assertIn('無効',self.ask('/research-confirm '+token))
 def test_cancel_invalidates(self):
  token=self.review();self.ask('キャンセル');self.assertIn('無効',self.ask('/research-confirm '+token))
 def test_deleted_history_invalidates(self):
  token=self.review();self.s.research_journal.delete(self.r['id']);self.assertIn('履歴が変わりました',self.ask('/research-confirm '+token))
 def test_expiry_and_topic_change(self):
  token=self.review();self.s.retry_review['expires']=0;self.assertIn('期限切れ',self.ask('/research-confirm '+token))
  token=self.review();self.ask('今日の予定は？');self.assertIn('無効',self.ask('/research-confirm '+token))
 def test_failed_fetch_no_old_answer(self):
  token=self.review();self.s.demo=False
  with patch.object(self.s.methods,'candidates',return_value=([],[])):
   answer=self.ask('/research-confirm '+token)
  self.assertNotIn('https://example.com/old',answer);self.assertEqual(len(self.s.research_journal.read()),1)
 def test_conflicting_method_fails_closed(self):
  self.r=self.s.research_journal.append('GoogleでOllamaを調べて','選択設定：自動（実際の提供元は出典を参照）',self.r['sources'])
  self.assertIn('実行していません',self.ask('/research-retry '+self.r['id']));self.assertIsNone(self.s.retry_review)
