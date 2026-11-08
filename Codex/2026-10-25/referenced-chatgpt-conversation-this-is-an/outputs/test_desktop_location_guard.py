import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_location_guard import DesktopService,asks_current_location

class LocationGuardTests(unittest.TestCase):
    def service(self):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup)
        s=DesktopService(tmp.name,demo=True);s.demo=False;self.addCleanup(s.close);return s
    def test_reported_sequence_retains_tomorrow(self):
        s=self.service()
        with patch('tomeris_weather_service.fetch_weather',return_value='平塚市の明日の予報') as weather,patch('tomeris_auto_research_v029.DesktopService.chat',side_effect=AssertionError('must not call model')):
            s.web_chat('明日の天気は？','test',automatic=True)
            answer=s.web_chat('現在地','test',automatic=True)
            self.assertIn('取得していません',answer);self.assertIn('明日',answer);self.assertNotIn('東京都荒川区',answer);weather.assert_not_called()
            self.assertEqual(s.pending_weather,'明日')
            s.web_chat('平塚市','test',automatic=True);weather.assert_called_once_with('平塚市','明日')
    def test_location_questions_do_not_go_to_model(self):
        s=self.service()
        with patch('tomeris_auto_research_v029.DesktopService.chat',side_effect=AssertionError('must not call model')):
            for text in ('現在地は？','今いる場所を教えて','ここはどこ？'):
                self.assertIn('取得していない',s.chat(text,'test'))
            self.assertIn('明日',s.report('現在地の明日の天気は？'))
    def test_today_can_replace_tomorrow(self):
        s=self.service();s.pending_weather='明日'
        self.assertIn('今日',s.web_chat('現在地の今日の天気','test',automatic=True));self.assertEqual(s.pending_weather,'今日')
    def test_unrelated_questions_are_not_location_requests(self):
        for text in ('アイアンマンについて調べて','平塚市','明日の天気は？','計算: 1+2'):
            self.assertFalse(asks_current_location(text))
