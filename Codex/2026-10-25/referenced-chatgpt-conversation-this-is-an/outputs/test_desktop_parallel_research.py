import unittest,threading
from types import SimpleNamespace
from unittest.mock import patch
from tomeris_parallel_research_v086 import ParallelMethods,concise_report,overview_excerpts

class ParallelResearchTests(unittest.TestCase):
 def base(self,question='光合成について調べて'):
  return SimpleNamespace(mode='自動',question_context=question,brave_key='',resolved=None)
 def test_jobs_are_concurrent_and_urls_deduplicated(self):
  barrier=threading.Barrier(2,timeout=3)
  row=dict(title='光合成',url='https://example.org/a')
  def wiki(q):barrier.wait();return row
  def web(q):barrier.wait();return [row,dict(title='別資料',url='https://example.org/b')]
  with patch('tomeris_parallel_research_v086.resolve_title',side_effect=wiki),patch('tomeris_parallel_research_v086.search_web',side_effect=web):
   rows,notes=ParallelMethods(self.base()).candidates('光合成')
  self.assertEqual(len(rows),2);self.assertIn('並行検索：2経路',notes[0])
 def test_failure_does_not_erase_other_result(self):
  with patch('tomeris_parallel_research_v086.resolve_title',side_effect=OSError()),patch('tomeris_parallel_research_v086.search_web',return_value=[dict(url='https://example.org/a')]):
   rows,notes=ParallelMethods(self.base()).candidates('光合成')
  self.assertEqual(len(rows),1);self.assertTrue(any('取得失敗' in n for n in notes))
 def test_volatile_request_does_not_use_encyclopedia(self):
  with patch('tomeris_parallel_research_v086.resolve_title') as wiki,patch('tomeris_parallel_research_v086.search_web',return_value=[]) as web:
   ParallelMethods(self.base('現在の料金')).candidates('料金');wiki.assert_not_called();self.assertEqual(web.call_count,2)
 def test_explicit_provider_uses_original_method(self):
  base=self.base();base.mode='Wikipedia（日本語）';base.candidates=lambda q: (['指定'],[])
  self.assertEqual(ParallelMethods(base).candidates('query')[0],['指定'])
 def test_summary_requires_verbatim_and_stable_citations(self):
  page=dict(title='資料',url='https://example.org/a',text='根拠のある文章です。')
  items=[dict(page=page,excerpts=['捏造した文章です。','根拠のある文章です。']),dict(page=page,excerpts=['根拠のある文章です。'])]
  answer=concise_report('調査対象：対象\n取得日時：時刻\n\n本文',items)
  self.assertNotIn('捏造',answer);self.assertIn('[1]',answer);self.assertNotIn('[2]',answer)
  self.assertIn('出典は1件',answer)
 def test_overview_skips_notices_and_navigation(self):
  definition='光合成とは、光のエネルギーを利用して有機物を作る反応です。'
  page=dict(text='トップ > 光合成の仕組み完全解説！\n今回は「光合成」について学習しましょう！\n'+definition)
  self.assertEqual(overview_excerpts(page,'光合成'),[definition])
