import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from tomeris_overview_resolution import resolve_title,ResolvedMethods
from tomeris_research_router import DesktopService

class ResolutionTests(unittest.TestCase):
 def test_provider_redirect_and_disambiguation(self):
  with patch('tomeris_overview_resolution.json_request',return_value={'query':{'pages':[{'pageid':7,'title':'マリ・キュリー'}]}}):
   self.assertEqual(resolve_title('マリー・キュリー')['title'],'マリ・キュリー')
  for page in ({'missing':True,'title':'不明'}, {'pageid':7,'title':'同名','pageprops':{'disambiguation':''}}):
   with patch('tomeris_overview_resolution.json_request',return_value={'query':{'pages':[page]}}):
    self.assertIsNone(resolve_title('同名'))
 def test_related_articles_not_identity(self):
  base=SimpleNamespace(mode='自動',question_context='マリー・キュリーについて調べて',
   candidates=lambda q:([dict(title='イレーヌ・キュリー',wiki_id=1)],[]))
  with patch('tomeris_overview_resolution.resolve_title',return_value=None):
   self.assertEqual(ResolvedMethods(base).candidates('マリー・キュリー')[0],[])
 def test_space_in_name_keeps_verbatim_lead(self):
  with tempfile.TemporaryDirectory() as d:
   s=DesktopService(Path(d),demo=True)
   try:
    s.methods.resolved=dict(title='徳川家康',requested_title='徳川家康')
    s.methods.question_context='徳川家康について調べて'
    lead='徳川 家康は、戦国時代から江戸時代初期の日本の武将・大名。'
    page=dict(title='徳川家康',provider='Wikipedia（二次資料）',text=lead+'\n==参考文献==\n徳川家康の本が出版されている。')
    self.assertEqual(s.extract_passages(page,'徳川家康'),[lead])
   finally:s.close()
