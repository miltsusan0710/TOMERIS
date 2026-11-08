import unittest
from copy import deepcopy
from tempfile import TemporaryDirectory
from unittest.mock import patch
from datetime import datetime
import tomeris_weather_data as data
from tomeris_weather_service import weather_request
from tomeris_conversation_preferences import DesktopService,conversation_style
from tomeris_capabilities import ContextProvider
from test_desktop_weather_data import PLACE,FORECAST

class WeatherConversationTests(unittest.TestCase):
    def test_day_after_tomorrow_parsing(self):
        for text in ('明後日の荒川区の天気は？','荒川区の明後日の天気は？'):
            self.assertEqual(weather_request(text),('荒川区','明後日'))
        self.assertEqual(weather_request('明後日の天気は？'),('','明後日'))
    def test_three_day_request_and_jst_date(self):
        forecast=deepcopy(FORECAST)
        forecast['daily']['time']=['2026-10-29','2026-10-30','2026-10-31']
        for key in ('weather_code','temperature_2m_max','temperature_2m_min','precipitation_probability_max'):forecast['daily'][key].append(12)
        with patch.object(data,'read_json',side_effect=[{'results':[PLACE]},forecast]) as read:
            answer=data.fetch_weather('平塚市','明後日',now=datetime(2026,10,29,0,5,tzinfo=data.JST))
            self.assertIn('2026-10-31',answer);self.assertIn('forecast_days=3',read.call_args.args[0])
        with self.assertRaises(data.WeatherError):data.fetch_weather('平塚市','昨日')
    def test_natural_followup_and_retry(self):
        with TemporaryDirectory() as folder:
            s=DesktopService(folder,demo=True);s.demo=False
            try:
                with patch('tomeris_weather_service.fetch_weather',side_effect=['明日の予報',data.WeatherError('通信失敗'),'明後日の予報']) as fetch:
                    s.web_chat('明日の荒川区の天気は？','none',automatic=True)
                    s.web_chat('明後日は？','none',automatic=True)
                    s.web_chat('荒川区','none',automatic=True)
                    self.assertEqual([c.args for c in fetch.call_args_list],[('荒川区','明日'),('荒川区','明後日'),('荒川区','明後日')])
            finally:s.close()
    def test_preferences_persist_edit_reset_and_not_fact_learning(self):
        with TemporaryDirectory() as folder:
            s=DesktopService(folder,demo=True)
            try:
                answer=s.web_chat('今後は回答を短くして','none',automatic=True);self.assertIn('覚えました',answer)
                self.assertIn('短く',conversation_style(s.store));count=len(s.store.data['memories'])
                s.chat('今後は回答を詳しくして','none');self.assertEqual(len(s.store.data['memories']),count);self.assertIn('具体的',conversation_style(s.store))
                self.assertIsNone(s.learn_preference('アイアンマンは漫画家です'))
            finally:s.close()
            s=DesktopService(folder,demo=True)
            try:
                self.assertIn('具体的',conversation_style(s.store));s.chat('会話の好みをリセット','none');self.assertEqual(conversation_style(s.store),'')
            finally:s.close()
    def test_style_enters_local_prompt_only(self):
        with patch('tomeris_capabilities.LocalProvider') as provider:
            ContextProvider('test',[],style='回答は短く。').generate([{'role':'system','content':'base'},{'role':'user','content':'質問'}])
            sent=provider.return_value.generate.call_args.args[0]
            self.assertEqual(sent[-1]['content'],'質問');self.assertIn({'role':'system','content':'回答は短く。'},sent)
