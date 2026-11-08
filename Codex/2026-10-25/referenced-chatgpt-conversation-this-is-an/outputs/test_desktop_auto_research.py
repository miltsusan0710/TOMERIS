import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from tomeris_auto_research import AutoMethods, DesktopService, instruction
import tomeris_search_methods as providers

class AutoResearchTests(unittest.TestCase):
    def test_explicit_and_topic_mentions(self):
        self.assertEqual(instruction('Googleでアイアンマンについて調べて'),('Google','アイアンマンについて調べて'))
        self.assertEqual(instruction('アイアンマンをWikipediaで調べて'),('Wikipedia（日本語）','アイアンマン'))
        self.assertEqual(instruction('Googleについて調べて')[0],None)
    def test_auto_and_fallback_restore(self):
        methods=AutoMethods()
        with patch.object(providers,'wikipedia_search',return_value=[]),patch.object(providers,'search_web',return_value=[]) as bing:
            methods.candidates('アイアンマン');bing.assert_called_once();self.assertEqual(methods.mode,'自動')
        methods.brave_key='TEST'
        with patch.object(providers,'brave_search',return_value=[{'url':'https://example.com/'}]) as brave,patch.object(providers,'wikipedia_search') as wiki:
            methods.candidates('最新ニュース');brave.assert_called_once();wiki.assert_not_called()
    def test_explicit_missing_key_no_fallback(self):
        with TemporaryDirectory() as folder:
            s=DesktopService(folder,demo=True);s.demo=False
            try:
                with patch.object(providers,'wikipedia_search') as wiki,patch.object(providers,'search_web') as bing:
                    answer=s.web_chat('Braveでアイアンマンについて調べて','test',automatic=True)
                    self.assertIn('未設定',answer);wiki.assert_not_called();bing.assert_not_called();self.assertEqual(s.methods.mode,'自動')
            finally:s.close()
    def test_google_weather_override_and_failure(self):
        with TemporaryDirectory() as folder:
            s=DesktopService(folder,demo=True);s.demo=False
            try:
                with patch('tomeris_auto_research.webbrowser.open',return_value=True) as browser:
                    answer=s.web_chat('Googleで荒川区の今日の天気を調べて','test',automatic=True)
                    self.assertIn('自動取得していません',answer);self.assertIn('google.com',browser.call_args.args[0])
                answer=s.web_chat('Geminiでアイアンマンについて調べて','test',automatic=True)
                self.assertIn('未設定',answer);self.assertIn('切り替えはしていません',answer)
            finally:s.close()
