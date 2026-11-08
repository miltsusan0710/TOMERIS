import unittest
from unittest.mock import patch,MagicMock
from tempfile import TemporaryDirectory
from pathlib import Path
import json
import tomeris_search_methods as methods
import tomeris_google_grounding as grounding
from tomeris_multisearch_service import DesktopService

WIKI={'query':{'search':[{'title':'アイアンマン','pageid':123,'snippet':'アイアンマンの説明'}]}}
GROUND={'status':'completed','steps':[{'type':'google_search_call','arguments':{'queries':['test']}},{'type':'google_search_result','result':[{'search_suggestions':'<div><a href="https://www.google.com/search?q=test">Google検索</a><script>bad()</script></div>'}]},{'type':'model_output','content':[{'type':'text','text':'Example factual statement.','annotations':[{'type':'url_citation','url':'https://example.com/','title':'Source','start_index':0,'end_index':26}]}]}]}
class MethodsTests(unittest.TestCase):
    def test_query_cleanup(self):
        self.assertEqual(methods.search_topic('アイアンマンについて調べて'),'アイアンマン')
        self.assertEqual(methods.search_topic('調査: Ollama'),'Ollama')
    def test_browser_queries_are_encoded(self):
        for engine in ('Google','Bing','DuckDuckGo'):
            url=methods.browser_search_url(engine,'アイアンマン & test');self.assertIn('%26',url);self.assertNotIn(' ',url)
        with self.assertRaises(methods.MethodError):methods.browser_search_url('unknown','test')
    def test_wiki_and_brave_parsing(self):
        with patch.object(methods,'json_request',return_value=WIKI):
            rows=methods.wikipedia_search('アイアンマン');self.assertEqual(rows[0]['wiki_id'],123);self.assertIn('ja.wikipedia.org/wiki/',rows[0]['url'])
        payload={'web':{'results':[{'title':'test','url':'https://example.com/','description':'description'},{'title':'bad','url':'file:///x'}]}}
        with patch.object(methods,'json_request',return_value=payload) as request:
            self.assertEqual(len(methods.brave_search('test','SECRET')),1)
            self.assertEqual(request.call_args.kwargs['headers'],{'X-Subscription-Token':'SECRET'})
        with patch.object(methods,'json_request') as request,self.assertRaises(methods.MethodError):methods.brave_search('test','')
        request.assert_not_called()
    def test_combined_survives_one_failed_provider(self):
        config=methods.SearchMethods();config.configure('併用（Wikipedia＋Brave）','','','gemini-3.8-flash')
        row=dict(title='test',url='https://example.com/',snippet='test')
        with patch.object(methods,'wikipedia_search',return_value=[row]):
            rows,notes=config.candidates('test');self.assertEqual(rows,[row]);self.assertTrue(any('未設定' in n for n in notes))
    def test_keys_are_not_written_and_not_auto_read(self):
        with TemporaryDirectory() as folder:
            s=DesktopService(folder,demo=True)
            try:
                s.configure_methods('Brave API','BRAVE_SECRET','GEMINI_SECRET','gemini-3.8-flash')
                for path in Path(folder).glob('*'):
                    if path.is_file() and path.name!='session.lock':self.assertNotIn(b'SECRET',path.read_bytes())
                self.assertEqual(s.methods.brave_key,'BRAVE_SECRET')
                s.configure_methods('Wikipedia（日本語）','','','gemini-3.8-flash');self.assertFalse(s.methods.brave_key)
            finally:s.close()
    def test_google_request_contains_only_current_question(self):
        with patch.object(grounding,'json_request',return_value=GROUND) as request:
            grounding.google_search('QUESTION','SECRET','gemini-3.8-flash')
            self.assertEqual(request.call_args.kwargs['payload'],{'model':'gemini-3.8-flash','input':'QUESTION','tools':[{'type':'google_search'}]})
            self.assertEqual(request.call_args.kwargs['headers'],{'x-goog-api-key':'SECRET'})
        with patch.object(grounding,'json_request') as request,self.assertRaises(methods.MethodError):grounding.google_search('question','','gemini-3.8-flash')
        request.assert_not_called()
    def test_grounding_citations_and_sandbox(self):
        html=grounding.render_grounding(GROUND,'<script>question</script>')
        self.assertIn('href="#source1"',html);self.assertIn('https://example.com/',html)
        self.assertIn('&lt;script&gt;question',html);self.assertNotIn('<script>question',html)
        self.assertIn('sandbox="allow-popups allow-popups-to-escape-sandbox"',html);self.assertNotIn('allow-scripts',html)
        self.assertIn('&lt;script&gt;bad()',html)
    def test_grounding_refuses_uncited_or_unsearched_response(self):
        with self.assertRaises(methods.MethodError):grounding.render_grounding({'steps':GROUND['steps'][2:]},'test')
        with self.assertRaises(methods.MethodError):grounding.render_grounding({'steps':GROUND['steps'][:2]},'test')
    def test_wikipedia_article_metadata(self):
        page={'query':{'pages':[{'title':'アイアンマン','fullurl':'https://ja.wikipedia.org/wiki/test','extract':'アイアンマンの説明がここに記載されています。'*10,'revisions':[{'timestamp':'2026-10-28T00:00:00Z'}]}]}}
        with patch.object(methods,'json_request',return_value=page):
            value=methods.wikipedia_page({'wiki_lang':'ja','wiki_id':123});self.assertIn('アイアンマン',value['text']);self.assertTrue(value['updated'])
    def test_http_errors_do_not_echo_keys(self):
        from urllib.error import HTTPError
        opener=MagicMock();opener.open.side_effect=HTTPError('https://api.example.com/',403,'SECRET',{},None)
        with patch.object(methods,'build_opener',return_value=opener),self.assertRaises(methods.MethodError) as caught:methods.json_request('https://api.example.com/',headers={'token':'SECRET'})
        self.assertNotIn('SECRET',str(caught.exception));self.assertIn('403',str(caught.exception))

