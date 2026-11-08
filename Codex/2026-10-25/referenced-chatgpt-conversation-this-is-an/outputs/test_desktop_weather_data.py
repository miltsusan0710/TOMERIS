import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory
from datetime import datetime
from copy import deepcopy
import tomeris_weather_data as data
import tomeris_weather_service as service

PLACE=dict(name='平塚市',admin1='神奈川県',admin2='平塚市',country_code='JP',latitude=35.32785,longitude=139.33736)
NOW=datetime(2026,10,28,12,tzinfo=data.JST)
FORECAST=dict(timezone='Asia/Tokyo',daily=dict(time=['2026-10-28','2026-10-29'],weather_code=[1,3],temperature_2m_max=[20.2,16.4],temperature_2m_min=[11,9.8],precipitation_probability_max=[27,32]),daily_units=dict(time='iso8601',weather_code='wmo code',temperature_2m_max='°C',temperature_2m_min='°C',precipitation_probability_max='%'))

class WeatherDataTests(unittest.TestCase):
    def test_render_exact_date_values(self):
        with patch.object(data,'read_json',side_effect=[{'results':[PLACE]},FORECAST]):
            answer=data.fetch_weather('平塚市',now=NOW)
            for value in ('2026-10-28','20.2℃','27％','神奈川県 平塚市','Open-Meteo'):self.assertIn(value,answer)
        with patch.object(data,'read_json',side_effect=[{'results':[PLACE]},FORECAST]):
            self.assertIn('2026-10-29',data.fetch_weather('平塚市','明日',now=NOW))
    def test_ward_fallback_requires_admin_match(self):
        ward=dict(name='荒川',admin1='東京都',admin2='荒川区',country_code='JP',latitude=35.73825,longitude=139.78047)
        wrong=dict(ward,admin1='新潟県',admin2='新発田市')
        with patch.object(data,'read_json',side_effect=[{},dict(results=[wrong,ward])]):
            self.assertEqual(data.locate('東京都荒川区'),ward)
        with patch.object(data,'read_json',return_value={'results':[wrong]}),self.assertRaises(data.WeatherError):data.locate('荒川区')
    def test_ambiguous_region_rejected(self):
        other=dict(PLACE,admin1='別の県')
        with patch.object(data,'read_json',return_value={'results':[PLACE,other]}),self.assertRaises(data.WeatherError):data.locate('平塚市')
    def test_dates_units_and_null_validation(self):
        variants=[]
        x=deepcopy(FORECAST);x['daily']['time']=['2025-10-28'];variants.append(x)
        x=deepcopy(FORECAST);x['daily_units']['temperature_2m_max']='F';variants.append(x)
        x=deepcopy(FORECAST);x['daily']['precipitation_probability_max'][0]=101;variants.append(x)
        x=deepcopy(FORECAST);x['timezone']='UTC';variants.append(x)
        for x in variants:
            with patch.object(data,'read_json',side_effect=[{'results':[PLACE]},x]),self.assertRaises(data.WeatherError):data.fetch_weather('平塚市',now=NOW)
        x=deepcopy(FORECAST);x['daily']['temperature_2m_max'][0]=None
        with patch.object(data,'read_json',side_effect=[{'results':[PLACE]},x]):self.assertIn('最高気温：未取得',data.fetch_weather('平塚市',now=NOW))
    def test_request_parsing(self):
        for question,expected in [('今日の天気は？',('','今日')),('平塚市の今日の天気は？',('平塚市','今日')),('東京都荒川区の明日の天気を教えて',('東京都荒川区','明日'))]:
            self.assertEqual(service.weather_request(question),expected)
        self.assertIsNone(service.weather_request('天気APIについて比較して調べて'))
    def test_failure_then_another_region_never_calls_ai(self):
        with TemporaryDirectory() as folder:
            s=service.DesktopService(folder,demo=True);s.demo=False
            try:
                with patch.object(service,'fetch_weather',side_effect=[data.WeatherError('通信失敗'),'荒川区の予報']) as fetch,patch.object(s,'chat',side_effect=AssertionError('must not call model')):
                    s.web_chat('今日の天気は？','none',automatic=True)
                    self.assertIn('話題を保持',s.web_chat('平塚市','none',automatic=True))
                    self.assertEqual(s.web_chat('荒川区','none',automatic=True),'荒川区の予報')
                    self.assertEqual([c.args for c in fetch.call_args_list],[('平塚市','今日'),('荒川区','今日')])
                    self.assertEqual(s.pending_weather,'今日')
            finally:s.close()
    def test_topic_change_clears_and_success_allows_region_change(self):
        with TemporaryDirectory() as folder:
            s=service.DesktopService(folder,demo=True)
            try:
                s.web_chat('平塚市の明日の天気','none',automatic=True)
                self.assertIn('荒川区の明日',s.web_chat('荒川区','none',automatic=True))
                s.web_chat('計算: 1+2','none',automatic=True);self.assertIsNone(s.pending_weather)
                self.assertIn('画面確認用の応答',s.web_chat('荒川区','none',automatic=True))
            finally:s.close()
