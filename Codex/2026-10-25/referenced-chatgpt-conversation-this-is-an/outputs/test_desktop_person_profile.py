import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v061 import DesktopService
from tomeris_person_profile import introduction

KUN = dict(title='KUN', url='https://ja.wikipedia.org/wiki/KUN', text='KUN（くん）は、日本のYouTuber、元プロゲーマーとして活動する人物。\n\n== 著書 ==\n別の文章。')
MASU = dict(title='桝太一', url='https://ja.wikipedia.org/wiki/桝太一', text='桝 太一（ます たいち）は、日本の研究者、フリーアナウンサー。\n\n== 著書 ==\n桝太一が聞く科学の伝え方。')


class PersonProfileTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.s=DesktopService(Path(tmp.name), demo=True);self.addCleanup(self.s.close)
        self.s.demo=False

    def test_kun_role_is_validation_not_search_query(self):
        with patch('tomeris_person_profile.wikipedia_search', return_value=[dict(title='HAN-KUN'),dict(title='KUN')]) as search, patch('tomeris_person_profile.wikipedia_page', return_value=KUN) as fetch:
            self.s.web_chat('kunってだれ？','unused',automatic=True)
            answer=self.s.web_chat('ユーチューバー','unused',automatic=True)
        search.assert_called_once_with('kun');fetch.assert_called_once_with(dict(title='KUN'))
        self.assertIn('元プロゲーマー',answer)
        self.assertIn('今回は再取得していません',self.s.chat('その出典は？','unused'))

    def test_spaced_name_lead_selected_not_books(self):
        with patch('tomeris_person_profile.wikipedia_search', return_value=[dict(title='桝太一'),dict(title='番組')]), patch('tomeris_person_profile.wikipedia_page', return_value=MASU):
            answer=self.s.chat('桝太一て誰？','unused')
        self.assertIn('フリーアナウンサー',answer);self.assertNotIn('科学の伝え方',answer)
        self.assertEqual(1,len(self.s.research_journal.read()))

    def test_wrong_role_and_wrong_identity_rejected(self):
        self.assertEqual('',introduction(KUN,'KUN','歌手'))
        self.assertEqual('',introduction(dict(KUN,title='HAN-KUN'),'KUN',None))

    def test_ambiguous_exact_name_pages_not_combined(self):
        with patch('tomeris_person_profile.wikipedia_search', return_value=[dict(title='同名 (歌手)'),dict(title='同名 (俳優)')]), patch('tomeris_person_profile.wikipedia_page', side_effect=[dict(KUN,title='同名 (歌手)',text='同名は、日本で活動する歌手として紹介されている人物。'),dict(KUN,title='同名 (俳優)',text='同名は、日本で活動する俳優として紹介されている人物。')]):
            self.assertIn('一意に確認できません',self.s.chat('同名って誰？','unused'))
        self.assertIsNone(self.s.research_source_snapshot)

    def test_missing_intro_does_not_use_book_titles(self):
        self.assertEqual('',introduction(dict(MASU,text='桝太一の著書一覧です。\n== 著書 ==\n桝太一が聞く科学の伝え方。'),'桝太一',None))
