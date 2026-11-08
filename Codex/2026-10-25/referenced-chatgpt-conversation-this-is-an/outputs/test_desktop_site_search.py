import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
import tomeris_site_search as sites

class SiteSearchTests(unittest.TestCase):
    def test_user_exact_prompt_and_variants(self):
        for text in ['ジャービスに関するサイトを出して','ジャービスのサイトを教えて','ジャービスのURLを教えて','ジャービスのリンクを探して','ジャービスの公式サイトは？']:
            self.assertTrue(sites.site_request(text),text)
        self.assertEqual(sites.site_query('ジャービスに関するサイトを出して'),'ジャービス')
        self.assertFalse(sites.site_request('サイトを作る方法を説明して'))
        self.assertIsNone(sites.site_query('そのサイトを見せて'))
    def test_only_retrieved_relevant_unique_links(self):
        rows=[dict(title='ジャービス紹介',url='https://example.com/a',snippet='ジャービスに関する説明'),dict(title='duplicate',url='https://example.com/a#section',snippet='ジャービス'),dict(title='別の話題',url='https://example.org/',snippet='unrelated'),dict(title='ジャービス',url='file:///C:/x',snippet='test')]
        self.assertEqual(len(sites.retrieved_sites(rows,'ジャービス')),1)
    def test_auto_mode_never_uses_ai_or_memory_to_build_links(self):
        with TemporaryDirectory() as folder:
            s=sites.DesktopService(folder,demo=True);s.demo=False
            try:
                s.remember('SECRET','目標')
                rows=[dict(title='ジャービス紹介',url='https://example.com/a',snippet='ジャービスの説明')]
                with patch.object(sites,'search_web',return_value=rows) as search,patch.object(s,'chat',side_effect=AssertionError('No LLM fallback')):
                    answer=s.web_chat('ジャービスに関するサイトを出して','missing',True,True)
                    search.assert_called_once_with('ジャービス')
                    self.assertIn('https://example.com/a',answer);self.assertNotIn('SECRET',answer)
                    self.assertEqual(len(s.store.data['conversations']),1)
                before=s.memory_path.read_bytes()
                with patch.object(sites,'search_web',side_effect=sites.SearchError('通信失敗')):
                    self.assertIn('URLは表示しません',s.web_chat('ジャービスのサイトを出して','missing',automatic=True))
                self.assertEqual(before,s.memory_path.read_bytes())
            finally:s.close()
    def test_offline_mode_does_not_search(self):
        with TemporaryDirectory() as folder:
            s=sites.DesktopService(folder,demo=True)
            try:
                with patch.object(sites,'search_web') as search:
                    self.assertIn('切り替えて',s.chat('ジャービスのサイトを出して','missing'));search.assert_not_called()
            finally:s.close()
