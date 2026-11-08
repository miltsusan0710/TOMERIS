import json
import socket
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch,Mock
import tomeris_page_reader as reader
import tomeris_evidence_report as reports
from tomeris_grounded_summary import validate_summary

TEXT='Ollama runs models locally on your computer. This documentation explains how to install and use Ollama with local models.'
PAGE=dict(title='Ollama documentation',text=TEXT,published='2026-10-01',url='https://docs.ollama.com/')
ROW=dict(title='Ollama documentation',snippet=TEXT,url=PAGE['url'])

class EvidenceTests(unittest.TestCase):
    def test_parser_removes_active_and_navigation_text(self):
        parser=reader.PageParser();parser.feed('<html><title>Ollama docs</title><script>DO BAD THINGS</script><nav>secret</nav><meta property="article:published_time" content="2026-10-01"><p>'+TEXT+'</p></html>')
        page=parser.result();self.assertNotIn('DO BAD',page['text']);self.assertNotIn('secret',page['text']);self.assertEqual(page['published'],'2026-10-01')
    def test_target_rejects_nonpublic_and_credentials(self):
        for address in ['127.0.0.1','10.0.0.1','169.254.169.254','::1']:
            with patch.object(socket,'getaddrinfo',return_value=[(2,1,6,'',(address,443))]),self.assertRaises(reader.PageError):reader.target('https://example.com/')
        for url in ['file:///x','http://u:p@example.com/','https://example.com:8000/']:
            with self.assertRaises(reader.PageError):reader.target(url)
    def test_redirect_revalidates_destination(self):
        response=Mock(status=302);response.getheader.return_value='http://127.0.0.1/'
        conn=Mock();conn.getresponse.return_value=response
        address=[(2,1,6,'',('8.8.8.8',443))]
        with patch.object(socket,'getaddrinfo',side_effect=[address,[(2,1,6,'',('127.0.0.1',80))]]),patch.object(reader,'PublicHTTPS',return_value=conn),self.assertRaises(reader.PageError):reader.fetch_page('https://example.com/')
        conn.close.assert_called_once()
    def test_reader_does_not_fetch_binary_or_excessive_data(self):
        for mime,payload in [('application/pdf',b'x'),('text/html',b'x'*1000001)]:
            response=Mock(status=200);response.getheader.side_effect=lambda key,default=None: mime if key=='Content-Type' else 'identity'
            response.read1.side_effect=[payload,b''];conn=Mock();conn.getresponse.return_value=response
            with patch.object(reader,'target',return_value=(reader.urlsplit('https://example.com/'),'example.com','8.8.8.8')),patch.object(reader,'PublicHTTPS',return_value=conn),self.assertRaises(reader.PageError):reader.fetch_page('https://example.com/')
    def test_summary_requires_existing_quote_source_and_numbers(self):
        pages=[dict(page=PAGE,excerpts=[TEXT])]
        point=dict(source=1,text='Ollamaはローカルでモデルを実行します。',quote=TEXT)
        self.assertIn('[1]',validate_summary(json.dumps(dict(points=[point])),pages))
        for change in [dict(source=9),dict(quote='This quote was never present in the retrieved original source.'),dict(text='Ollamaは99倍高速です。'),dict(text='https://invented.example/')]:
            self.assertIsNone(validate_summary(json.dumps(dict(points=[dict(point,**change)])),pages))
    def test_report_uses_pages_and_no_model_if_unavailable(self):
        with TemporaryDirectory() as folder:
            s=reports.DesktopService(folder,demo=True);s.demo=False
            try:
                s.remember('SECRET','その他')
                with patch.object(reports,'search_web',return_value=[ROW]) as search,patch.object(reports,'fetch_page',return_value=PAGE) as fetch:
                    answer=s.web_chat('Ollamaについて調べて','missing',True,True)
                    self.assertIn(TEXT.split('. ')[0],answer);self.assertIn(PAGE['url'],answer);self.assertNotIn('SECRET',str(search.call_args_list))
                    fetch.assert_called_once_with(PAGE['url']);self.assertIn('掲載日',answer)
            finally:s.close()
    def test_all_pages_unavailable_never_invents_answer(self):
        with TemporaryDirectory() as folder:
            s=reports.DesktopService(folder,demo=True);s.demo=False
            try:
                before=s.memory_path.read_bytes()
                with patch.object(reports,'search_web',return_value=[ROW]),patch.object(reports,'fetch_page',side_effect=reader.PageError('HTTP 403')):
                    answer=s.research('Ollama','missing');self.assertIn('根拠を取得できません',answer);self.assertIn('HTTP 403',answer)
                self.assertEqual(before,s.memory_path.read_bytes())
            finally:s.close()
    def test_ambiguous_jarvis_asks_before_search(self):
        with TemporaryDirectory() as folder:
            s=reports.DesktopService(folder,demo=True);s.demo=False
            try:
                with patch.object(reports,'search_web',return_value=[]) as search:
                    answer=s.web_chat('ジャービスに関するサイトを出して','missing',automatic=True)
                    self.assertIn('どの',answer);search.assert_not_called()
                    s.web_chat('アイアンマン','missing',automatic=True)
                    self.assertIn('アイアンマン',search.call_args_list[0].args[0]);self.assertFalse(s.pending_subject)
            finally:s.close()
    def test_math_and_weather_are_preserved(self):
        with TemporaryDirectory() as folder:
            s=reports.DesktopService(folder,demo=True)
            try:
                self.assertIn('結果：3',s.web_chat('1+2','missing',automatic=False))
                self.assertIn('市区町村',s.web_chat('今日の天気は？','missing',automatic=True))
                self.assertIn('平塚市',s.web_chat('平塚市','missing',automatic=True))
            finally:s.close()

    def test_direct_url_bypasses_search_and_keeps_source(self):
        with TemporaryDirectory() as folder:
            s=reports.DesktopService(folder,demo=True);s.demo=False
            try:
                with patch.object(reports,'search_web') as search,patch.object(reports,'fetch_page',return_value=PAGE) as fetch:
                    answer=s.web_chat('https://docs.ollama.com/ 内容を教えて','missing',automatic=True)
                    search.assert_not_called();fetch.assert_called_once_with('https://docs.ollama.com/')
                    self.assertIn(PAGE['url'],answer)
            finally:s.close()
    def test_invalid_summary_is_not_displayed(self):
        with TemporaryDirectory() as folder:
            s=reports.DesktopService(folder,demo=True);s.demo=False;s.model_names=['test']
            try:
                with patch.object(reports,'search_web',return_value=[ROW]),patch.object(reports,'fetch_page',return_value=PAGE),patch.object(reports,'summarize',return_value=None):
                    answer=s.research('Ollama','test')
                    self.assertNotIn('【資料に基づく整理',answer);self.assertIn('根拠原文だけ',answer)
            finally:s.close()

    def test_summary_evidence_ids_attach_original_without_model_quotes(self):
        pages=[dict(page=PAGE,excerpts=[TEXT])]
        good=json.dumps({'points':[{'text':'Ollamaでローカルモデルを実行できます。','evidence':'S1P1'}]})
        self.assertIn(TEXT,validate_summary(good,pages))
        bad=json.dumps({'points':[{'text':'説明','evidence':'S9P1'}]})
        self.assertIsNone(validate_summary(bad,pages))
