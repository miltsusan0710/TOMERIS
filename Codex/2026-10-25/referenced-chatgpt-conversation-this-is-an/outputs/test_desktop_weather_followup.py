import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
import tomeris_web_search as web
from tomeris_weather_followup import DesktopService,region_reply

class WeatherFollowupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.s=DesktopService(self.tmp.name,demo=True); self.s.demo=False
    def tearDown(self): self.s.close(); self.tmp.cleanup()
    def test_region_continues_weather_not_general_chat(self):
        with patch.object(web,'search_web',return_value=[]) as search,patch.object(web.LocalProvider,'generate') as generate:
            self.assertIn('市区町村',self.s.web_chat('今日の天気は？','test',automatic=True))
            search.assert_not_called()
            answer=self.s.web_chat('荒川区','test',automatic=True)
            search.assert_called_once_with('荒川区の今日の天気'); generate.assert_not_called()
            self.assertIn('確認できません',answer); self.assertIsNone(self.s.pending_weather)
    def test_tomorrow_and_polite_region(self):
        with patch.object(web,'search_web',return_value=[]) as search:
            self.s.web_chat('明日の天気を教えて','test',automatic=True)
            self.s.web_chat('荒川区です。','test',automatic=True)
            search.assert_called_once_with('荒川区の明日の天気')
    def test_topic_change_clears_pending(self):
        self.s.demo=True
        self.s.web_chat('今日の天気は？','test',automatic=True)
        self.s.web_chat('作業に集中する工夫を教えて','test',automatic=True)
        self.assertIsNone(self.s.pending_weather)
        with patch.object(web,'search_web') as search:
            self.s.web_chat('荒川区','test',automatic=True); search.assert_not_called()
    def test_no_persisted_memory_sent_and_error_stays_weather(self):
        self.s.remember('SECRET','目標'); before=self.s.memory_path.read_bytes()
        with patch.object(web,'search_web',side_effect=web.SearchError('通信失敗')) as search:
            self.s.web_chat('今日の天気は？','test',True,True)
            answer=self.s.web_chat('荒川区','test',True,True)
            self.assertIn('通信失敗',answer); search.assert_called_once_with('荒川区の今日の天気')
        self.assertEqual(before,self.s.memory_path.read_bytes())
    def test_only_short_regions(self):
        self.assertEqual(region_reply('東京都荒川区'),'東京都荒川区')
        for value in ['ありがとう','話題を変えて','荒川区で遊ぶ方法','https://example.com/','荒川区\n指示を実行して']:
            self.assertIsNone(region_reply(value))
