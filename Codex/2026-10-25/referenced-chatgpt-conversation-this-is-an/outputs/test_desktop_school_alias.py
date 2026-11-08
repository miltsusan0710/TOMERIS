import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from tomeris_school_alias import DesktopService
from tomeris_topic_flow import DesktopService as BaseService
from tomeris_overview import OverviewMethods
from types import SimpleNamespace

class SchoolAliasTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.s.close)
 def test_verified_alias_rewrites_whole_request(self):
  with patch.object(BaseService,'report',return_value='原文') as report:answer=self.s.report('本所高校について調べて')
  self.assertEqual(report.call_args.args[0],'東京都立本所高等学校について調べて');self.assertIn('正式名称',answer)
  self.assertEqual(self.s.school_topic,'東京都立本所高等学校')
  with patch.object(self.s,'report',return_value='未確認') as followup:self.s.prepare_context('校長は誰？')
  self.assertEqual(followup.call_args.args[0],'東京都立本所高等学校 現在の校長 公式')
 def test_unknown_school_and_explicit_method_not_changed(self):
  for query in ('本庄高校について調べて','本所工科高校について調べて','Googleで本所高校について調べて'):
   with patch.object(BaseService,'report',return_value='原文') as report:self.s.report(query)
   self.assertEqual(report.call_args.args[0],query)
 def test_canonical_overview_excludes_similar_school(self):
  rows=[dict(title='東京都立本所高等学校',wiki_id=1),dict(title='東京都立本所工科高等学校',wiki_id=2)]
  base=SimpleNamespace(mode='自動',question_context='東京都立本所高等学校について調べて',candidates=lambda _: (rows,[]))
  result,_=OverviewMethods(base).candidates('東京都立本所高等学校')
  self.assertEqual([r['wiki_id'] for r in result],[1])
