import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v065 import DesktopService

INTRO='トニー・スタークは、物語に登場する主人公として紹介されています。'
DETAIL='トニー・スタークは、別作品では異なる年齢で登場すると説明されています。'


class OverviewTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.s=DesktopService(Path(tmp.name),demo=True);self.addCleanup(self.s.close)
        self.s.demo=False

    def test_overview_only_exact_article_lead(self):
        rows=[dict(title='アイアンマン',url='https://ja.wikipedia.org/wiki/other',snippet=DETAIL,wiki_id=1),dict(title='トニー・スターク',url='https://ja.wikipedia.org/wiki/tony',snippet=INTRO,wiki_id=2)]
        page=dict(title='トニー・スターク',url=rows[1]['url'],text=INTRO+'\n== 別作品 ==\n'+DETAIL,published='',provider='Wikipedia（二次資料）')
        with patch('tomeris_research_learning.BaseMethods.candidates',return_value=(rows,[])),patch('tomeris_evidence_v029.wikipedia_page',return_value=page) as fetch:
            answer=self.s.web_chat('トニースタークについて調べて','unused',automatic=True)
        fetch.assert_called_once_with(rows[1])
        self.assertIn(INTRO,answer);self.assertNotIn(DETAIL,answer)

    def test_specific_question_keeps_full_passages(self):
        self.s.methods.question_context='トニースタークの年齢の違いについて調べて'
        page=dict(title='トニー・スターク',text=INTRO+'\n== 別作品 ==\n'+DETAIL,provider='Wikipedia（二次資料）')
        self.assertIn(DETAIL,self.s.extract_passages(page,'トニースターク'))

    def test_no_matching_title_keeps_candidates(self):
        rows=[dict(title='解説',url='https://example.com/',snippet=INTRO)]
        self.s.methods.question_context='トニースタークについて調べて'
        with patch('tomeris_research_learning.BaseMethods.candidates',return_value=(rows,[])):
            self.assertEqual(rows,self.s.methods.candidates('トニースターク')[0])

    def test_configuration_forwarded(self):
        self.s.methods.configure('自動')
        self.s.methods.question_context='質問'
        self.assertEqual('質問',self.s.methods._base.question_context)
        self.assertIs(self.s.methods.catalogue,self.s.catalogue)
