import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
import tomeris_auto_research_v0281 as routing
import tomeris_search_methods as providers

class ResearchFollowupTests(unittest.TestCase):
    def service(self):
        folder=TemporaryDirectory();self.addCleanup(folder.cleanup)
        service=routing.DesktopService(folder.name,demo=True);service.demo=False;self.addCleanup(service.close)
        return service
    def test_negative_or_conflicting_instructions_send_nothing(self):
        s=self.service()
        with patch.object(routing.webbrowser,'open') as browser,patch.object(providers,'wikipedia_search') as wiki:
            for text in ('GoogleではなくWikipediaでアイアンマンを調べて','GoogleとWikipediaで調べて','Googleで調べて、Bingで確認して'):
                self.assertIn('外部へ送信していません',s.web_chat(text,'test',automatic=True))
            browser.assert_not_called();wiki.assert_not_called()
        self.assertIsNone(routing.instruction('Googleでできることを教えて')[0])
    def test_method_only_then_topic_and_cancel(self):
        s=self.service()
        with patch.object(routing.webbrowser,'open',return_value=True) as browser:
            self.assertIn('何を調べますか',s.web_chat('Googleで調べて','test',automatic=True));browser.assert_not_called()
            self.assertIn('指定方法：Google',s.web_chat('アイアンマン','test',automatic=True));browser.assert_called_once()
            s.web_chat('Googleで調べて','test',automatic=True)
            self.assertIn('取り消し',s.web_chat('キャンセル','test',automatic=True));self.assertIsNone(s.pending_method)
    def test_new_instruction_replaces_pending(self):
        s=self.service();s.web_chat('Googleで調べて','test',automatic=True)
        with patch.object(routing.webbrowser,'open') as browser,patch.object(providers,'wikipedia_search',return_value=[]):
            s.web_chat('Wikipediaでアイアンマンについて調べて','test',automatic=True);browser.assert_not_called()
    def test_site_intent_survives_query_cleanup(self):
        s=self.service();s.methods.brave_key='TEST'
        with patch.object(providers,'brave_search',return_value=[dict(title='test',url='https://example.com/',snippet='test')]) as brave,patch('tomeris_multisearch_service.fetch_page',side_effect=routing.PageError('test')):
            s.report('Ollamaの公式サイトを出して');brave.assert_called_once()
        self.assertEqual(s.methods.question_context,'');self.assertEqual(s.methods.mode,'自動')
    def test_direct_url_handoff(self):
        s=self.service()
        page=dict(title='ページ',url='https://example.com/',text='公開された本文です。'*300,published='')
        with patch.object(routing,'fetch_page',return_value=page) as fetch:
            answer=s.web_chat('https://example.com/','test',automatic=True)
            self.assertIn('冒頭・最大1800文字',answer);self.assertLess(len(answer),2100);fetch.assert_called_once()
        with patch.object(routing,'fetch_page',side_effect=routing.PageError('非公開アドレス')):
            self.assertIn('取得できません',s.report('http://127.0.0.1/'))
    def test_explicit_wiki_url_does_not_read_other_source(self):
        s=self.service()
        with patch.object(routing,'fetch_page') as fetch:
            answer=s.report('Wikipediaでhttps://example.com/を調べて');fetch.assert_not_called();self.assertIn('対象名',answer)
