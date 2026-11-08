import unittest
from unittest.mock import patch,Mock,MagicMock
from tempfile import TemporaryDirectory
import tomeris_web_search as web

XML=b'<rss><channel><item><title>Ollama official</title><link>https://ollama.com/</link><description>Run models locally</description></item></channel></rss>'
class WebTests(unittest.TestCase):
    def test_parser_and_unsafe_urls(self):
        self.assertEqual(web.parse_results(XML)[0]['url'],'https://ollama.com/')
        for url in ['file:///a','javascript:alert(1)','http://localhost/','http://127.0.0.1/','http://192.168.1.1/','https://x:y@example.com/']:
            self.assertFalse(web.public_url(url))
        self.assertEqual(web.parse_results(XML.replace(b'https://ollama.com/',b'file:///a')),[])
    def test_bad_response(self):
        for data in [b'<html>captcha</html>',b'bad',b'<!DOCTYPE x><rss/>',b'x'*1000001]:
            with self.assertRaises(web.SearchError): web.parse_results(data)
    def test_routing(self):
        self.assertTrue(web.needs_search('最新のOllamaを調べて')); self.assertFalse(web.needs_search('気分転換の工夫を3つ'))
        self.assertTrue(web.location_missing('今日の天気は？')); self.assertFalse(web.location_missing('新宿区の今日の天気は？'))
    def test_irrelevant_weather_not_used(self):
        self.assertEqual(web.relevant_results('新宿区 天気',[dict(title='新宿観光',snippet='人気のお店',url='https://example.com')]),[])
        self.assertEqual(web.relevant_results('Python 公式',web.parse_results(XML)),[])
    def test_request_only_question_bounded_fixed_host(self):
        response=Mock(); response.status=200; response.read.return_value=XML
        opener=MagicMock(); opener.open.return_value.__enter__.return_value=response
        with patch.object(web,'build_opener',return_value=opener): web.search_web('Ollama')
        req=opener.open.call_args.args[0]
        self.assertEqual(req.full_url.split('?')[0],'https://www.bing.com/search')
        self.assertIn('q=Ollama',req.full_url); response.read.assert_called_once_with(1000001)
        with self.assertRaises(web.SearchError): web.NoRedirect().redirect_request(None,None,None,None,None,None)
    def test_privacy_and_failure(self):
        with TemporaryDirectory() as folder:
            s=web.DesktopService(folder,demo=True)
            try:
                s.remember('SECRET_MEMORY','目標'); s.store.add_conversation('SECRET_PAST','SECRET_ANSWER'); s.model_names=['test']; s.demo=False
                with patch.object(web,'search_web',return_value=web.parse_results(XML)) as search,patch.object(web,'LocalProvider') as provider:
                    provider.return_value.generate.return_value='ローカルでモデルを実行できます。[1]'
                    answer=s.web_chat('Ollamaを検索して','test',True)
                    search.assert_called_once_with('Ollamaを検索して')
                    prompt=str(provider.return_value.generate.call_args)
                    self.assertNotIn('SECRET',prompt); self.assertIn('https://ollama.com/',answer)
                before=s.memory_path.read_bytes()
                with patch.object(web,'search_web',side_effect=web.SearchError('通信失敗')),patch.object(web,'LocalProvider') as provider:
                    self.assertIn('回答は作っていません',s.web_chat('最新ニュース','test')); provider.assert_not_called()
                self.assertEqual(s.memory_path.read_bytes(),before)
                with patch.object(web,'search_web') as search:
                    self.assertIn('市区町村',s.web_chat('今日の天気は？','test')); search.assert_not_called()
                with patch.object(s,'chat',return_value='通常回答') as chat,patch.object(web,'search_web') as search:
                    self.assertEqual(s.web_chat('集中の工夫','test',True,True),'通常回答'); search.assert_not_called(); chat.assert_called_once_with('集中の工夫','test',True)
            finally:s.close()
    def test_model_unavailable_still_shows_sources(self):
        with TemporaryDirectory() as folder:
            s=web.DesktopService(folder,demo=True); s.demo=False
            try:
                with patch.object(web,'search_web',return_value=web.parse_results(XML)):
                    self.assertIn('https://ollama.com/',s.web_chat('Ollama','missing'))
            finally: s.close()

