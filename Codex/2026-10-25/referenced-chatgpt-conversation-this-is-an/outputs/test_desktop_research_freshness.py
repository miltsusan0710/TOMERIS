import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v057 import DesktopService
from tomeris_page_reader import PageError
from tomeris_web_search import SearchError

OLD = 'Ollamaは旧保存資料だけに存在する識別文を持つツールとして説明されています。'
NEW = 'Ollamaは今回取得した新しい説明文を持つツールとして紹介されています。'
URL = 'https://example.com/ollama'


class ResearchFreshnessTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.s = DesktopService(Path(tmp.name), demo=True)
        self.addCleanup(self.s.close)
        self.s.demo = False
        self.s.catalogue.save([dict(title='Ollama', url=URL, excerpt=OLD,
                                    retrieved='2000-01-01T00:00:00+09:00')], True)

    def ask(self):
        return self.s.web_chat('Ollamaについて調べて', 'unused', automatic=True)

    def test_saved_candidate_failure_no_old_excerpt_or_timestamp(self):
        before = self.s.catalogue.path.read_bytes()
        with patch('tomeris_research_learning.BaseMethods.candidates', return_value=([], [])), patch('tomeris_evidence_v029.fetch_page', side_effect=PageError('取得不可')) as fetch:
            answer = self.ask()
        fetch.assert_called_once_with(URL)
        self.assertNotIn(OLD, answer)
        self.assertNotIn('2000-01-01', answer)
        self.assertIn('確認日時（本文根拠未取得）', answer)
        self.assertNotIn('\n取得日時：', answer)
        self.assertEqual([], self.s.last_evidence_items)
        self.assertEqual([], self.s.research_journal.read())
        self.assertEqual(before, self.s.catalogue.path.read_bytes())
        self.assertEqual(answer, self.s.session_turns[-1][1])

    def test_success_then_failure_clears_previous_sources(self):
        with patch('tomeris_research_learning.BaseMethods.candidates', return_value=([], [])):
            with patch('tomeris_evidence_v029.fetch_page', return_value=dict(url=URL, title='Ollama', text=NEW, published='')):
                self.assertIn(NEW, self.ask())
            records = self.s.research_journal.read()
            with patch('tomeris_evidence_v029.fetch_page', side_effect=PageError('取得不可')):
                self.assertNotIn(NEW, self.ask())
        self.assertEqual(records, self.s.research_journal.read())
        self.assertIn('出典は確認できません', self.s.chat('その出典は？', 'unused'))

    def test_partial_success_only_new_evidence_is_reported(self):
        other = 'https://example.org/current'
        row = dict(title='Ollama', url=other, snippet=NEW)
        def fetch(url):
            if url == URL:
                raise PageError('旧URL取得不可')
            return dict(url=other, title='Ollama', text=NEW, published='')
        with patch('tomeris_research_learning.BaseMethods.candidates', return_value=([row], [])), patch('tomeris_evidence_v029.fetch_page', side_effect=fetch):
            answer = self.ask()
        self.assertIn(NEW, answer)
        self.assertNotIn(OLD, answer)
        self.assertIn('\n取得日時：', answer)
        self.assertEqual([other], [x['url'] for x in self.s.research_source_snapshot['sources']])

    def test_latest_search_failure_never_uses_saved_candidates(self):
        with patch('tomeris_research_learning.search_web', side_effect=SearchError('検索失敗')), patch.object(self.s.catalogue, 'candidates', side_effect=AssertionError('no cached candidates')), patch('tomeris_evidence_v029.fetch_page', side_effect=AssertionError('no fetch')):
            answer = self.s.web_chat('Ollamaの最新ニュースを調べて', 'unused', automatic=True)
        self.assertNotIn(OLD, answer)
        self.assertIn('本文根拠未取得', answer)

    def test_unrelated_retrieved_body_not_replaced_with_saved_snippet(self):
        with patch('tomeris_research_learning.BaseMethods.candidates', return_value=([], [])), patch('tomeris_evidence_v029.fetch_page', return_value=dict(url=URL, title='別の話', text='本文には対象と関係ない情報だけが書かれています。', published='')):
            answer = self.ask()
        self.assertNotIn(OLD, answer)
        self.assertIn('本文根拠未取得', answer)
