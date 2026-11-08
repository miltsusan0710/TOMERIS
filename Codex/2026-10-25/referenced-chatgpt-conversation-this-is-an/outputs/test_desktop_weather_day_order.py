import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_weather_service import weather_request
from tomeris_weather_data import WeatherError
from tomeris_location_guard import DesktopService

class WeatherDayOrderTests(unittest.TestCase):
    def test_day_before_and_after_city(self):
        for text in ('明日の荒川区の天気は？','荒川区の明日の天気は？','明日荒川区の天気','明日 東京都荒川区の天気を教えて'):
            with self.subTest(text=text):
                place,day=weather_request(text);self.assertEqual(day,'明日');self.assertIn(place,('荒川区','東京都荒川区'))
        self.assertEqual(weather_request('今日の荒川区の天気は？'),('荒川区','今日'))
        self.assertEqual(weather_request('荒川区の天気は？'),('荒川区','今日'))
        self.assertEqual(weather_request('明日の天気は？'),('','明日'))
    def test_failed_city_retry_retains_tomorrow(self):
        with TemporaryDirectory() as folder:
            s=DesktopService(folder,demo=True);s.demo=False
            try:
                with patch('tomeris_weather_service.fetch_weather',side_effect=[WeatherError('地域を一意に確認できませんでした。'),'明日の予報']) as fetch:
                    first=s.web_chat('明日の荒川区の天気は？','test',automatic=True)
                    self.assertIn('荒川区の明日の予報',first);self.assertNotIn('今日',first)
                    answer=s.web_chat('荒川区','test',automatic=True)
                    self.assertEqual(answer,'明日の予報')
                    self.assertEqual([c.args for c in fetch.call_args_list],[('荒川区','明日'),('荒川区','明日')])
            finally:s.close()
