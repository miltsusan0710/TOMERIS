import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from tomeris_school_location import DesktopService,subject

class SchoolLocationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.s.close);self.s.demo=False
 def test_both_reported_questions_and_other_variants(self):
  for q in ('荒川区立第一中学校はどこ？','本所高校はどこ？','東京大学の住所を教えて'):
   self.assertIsNotNone(subject(q))
  for q in ('学校はどこにあるかという物語を書いて','「本所高校はどこ？」を英訳して','今どこ？'):self.assertIsNone(subject(q))
 def test_official_line_without_people_fabrication(self):
  page=dict(title='東京都立本所高等学校',text='東京都立学校一覧\n住所　東京都墨田区向島3-37-25\n校長：試験人物',url='https://www.metro.ed.jp/honjo-h/access/access.html')
  with patch('tomeris_school_location.fetch_page',return_value=page):answer=self.s.web_chat('本所高校はどこ？','unused',automatic=True)
  self.assertIn('向島3-37-25',answer);self.assertNotIn('試験人物',answer);self.assertIn('出典',answer)
  self.assertNotIn('学校一覧',answer)
 def test_failure_never_uses_model(self):
  with patch('tomeris_school_location.fetch_page',side_effect=OSError('offline')),patch('tomeris_capabilities.LocalProvider.generate',side_effect=AssertionError('model')):
   answer=self.s.chat('荒川区立第一中学校はどこ？','unused')
  self.assertIn('確認できません',answer);self.assertNotIn('1-1',answer)
 def test_unknown_school_routes_to_research(self):
  with patch.object(self.s,'report',return_value='evidence') as report:
   self.assertEqual(self.s.web_chat('東京大学はどこ？','unused',automatic=True),'evidence')
  self.assertEqual(report.call_args.args[0],'東京大学 所在地 公式')
 def test_explicit_method_is_respected(self):
  with patch.object(self.s,'report',return_value='specified') as report:
   self.assertEqual(self.s.web_chat('Googleで本所高校はどこ？','unused',automatic=True),'specified')
  self.assertEqual(report.call_args.args[0],'Googleで本所高校はどこ？')
