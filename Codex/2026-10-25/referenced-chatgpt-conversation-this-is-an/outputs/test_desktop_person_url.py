import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v062 import DesktopService
from tomeris_page_reader import PageError


class PersonURLTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.s=DesktopService(Path(tmp.name),demo=True);self.addCleanup(self.s.close)
        self.s.demo=False

    def pending(self):
        with patch('tomeris_person_profile.wikipedia_search',return_value=[]):
            self.s.chat('山田太郎って誰？','unused')
        self.assertEqual('山田太郎',self.s.pending_profile_url)

    def test_url_follows_person_and_source_is_current(self):
        self.pending()
        text='山田太郎は、このページで研究者として紹介されている人物です。'
        with patch('tomeris_evidence_v029.fetch_page',return_value=dict(title='プロフィール',url='https://example.com/person',text=text,published='')) as fetch, patch.object(self.s.methods,'candidates',side_effect=AssertionError('direct URL only')):
            answer=self.s.web_chat('https://example.com/person','unused',automatic=True)
        fetch.assert_called_once_with('https://example.com/person')
        self.assertIn(text,answer);self.assertIn('山田太郎',answer)
        self.assertIn('公式資料と認定したわけではありません',answer)
        self.assertIn('example.com/person',self.s.chat('その出典は？','unused'))

    def test_unrelated_page_not_used_as_profile(self):
        self.pending()
        with patch('tomeris_evidence_v029.fetch_page',return_value=dict(title='別人',url='https://example.com/person',text='別の人物についてのみ紹介している資料です。',published='')):
            answer=self.s.chat('https://example.com/person','unused')
        self.assertIn('本文根拠未取得',answer)
        self.assertIsNone(self.s.research_source_snapshot)

    def test_private_url_rejected_before_fetch(self):
        self.pending()
        with patch('tomeris_evidence_v029.fetch_page',side_effect=AssertionError('no network')):
            self.assertIn('取得していません',self.s.chat('http://127.0.0.1/','unused'))

    def test_failure_leaves_no_old_evidence(self):
        self.pending()
        with patch('tomeris_evidence_v029.fetch_page',side_effect=PageError('取得不可')):
            answer=self.s.chat('https://example.com/person','unused')
        self.assertIn('本文根拠未取得',answer)
        self.assertIsNone(self.s.research_source_snapshot)

    def test_cancel_or_unrelated_turn_clears_name(self):
        for text in ('キャンセル','別の話','今日の予定は？'):
            self.pending();self.s.chat(text,'unused')
            self.assertIsNone(self.s.pending_profile_url)
