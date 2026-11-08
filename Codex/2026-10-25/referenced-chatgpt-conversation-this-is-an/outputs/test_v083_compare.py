import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
import tomeris_compare_v083 as cmp
import tomeris_v083 as app

class CompareTests(unittest.TestCase):
    def factory(self, failure=None):
        self.seen=[]
        def factory(model='a',**kwargs):
            provider=Mock()
            provider._request.return_value={'models':[{'name':'a','digest':'1'},{'name':'b','digest':'2'}]}
            def generate(messages):
                self.seen.append((model,deepcopy(messages)))
                messages.append({'role':'assistant','content':'MUTATION'})
                if model==failure:
                    raise app.ProviderError('unavailable')
                return 'answer '+model
            provider.generate.side_effect=generate
            return provider
        return factory

    def test_identical_context_and_isolation(self):
        messages=[{'role':'user','content':'question'}]
        with contextlib.redirect_stdout(io.StringIO()):
            results=cmp.compare(['a','b'],'question',messages,self.factory())
        self.assertEqual([x['status'] for x in results],['ok','ok'])
        self.assertEqual(self.seen[0][1],self.seen[1][1])
        self.assertEqual(messages,[{'role':'user','content':'question'}])

    def test_first_failure_still_shows_second(self):
        with contextlib.redirect_stdout(io.StringIO()):
            results=cmp.compare(['a','b'],'hi',[],self.factory('a'))
        self.assertEqual([x['status'] for x in results],['error','ok'])

    def test_duplicate_missing_alias_and_actions_rejected(self):
        factory=self.factory()
        for models,question in [(['a','a'],'hi'),(['a','missing'],'hi'),(['a','b'],'PCのファイルを削除して')]:
            with self.assertRaises(app.ProviderError):
                cmp.compare(models,question,[],factory)
        self.assertEqual(self.seen,[])
        provider=Mock()
        provider._request.return_value={'models':[{'name':'a','digest':'1'},{'name':'b','digest':'1'}]}
        with self.assertRaises(app.ProviderError):
            cmp.compare(['a','b'],'hi',[],lambda **kw:provider)

    def test_cloud_model_excluded(self):
        provider=Mock()
        provider._request.return_value={'models':[{'name':'local'},{'name':'remote-cloud'},{'name':'proxy','remote_model':'cloud-model'}]}
        self.assertEqual(list(cmp.list_models(provider)),['local'])

    def test_fabricated_actions_marked_replaced(self):
        provider=Mock()
        provider._request.return_value={'models':[{'name':'a'},{'name':'b'}]}
        provider.generate.return_value='PCのファイル削除を実行しました。'
        with contextlib.redirect_stdout(io.StringIO()):
            results=cmp.compare(['a','b'],'整理するコツは？',[],lambda **kw:provider)
        self.assertTrue(all(r['status']=='replaced' for r in results))
        self.assertTrue(all('未実行' in r['answer'] for r in results))

    def test_cli_comparison_separate_from_history_no_gemini(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            results=[{'model':n,'status':'ok','answer':'answer','seconds':1} for n in ['a','b']]
            with patch.object(app,'MEMORY_FILE',root/'memory.json'), patch.object(app,'CORE_FILE',root/'core.md'), patch.object(app,'KNOWLEDGE_DIR',root/'knowledge'), patch.object(app.OllamaProvider,'check',return_value=(True,'mock')), patch.object(app,'compare',return_value=results), patch.object(app.GeminiProvider,'generate',side_effect=AssertionError):
                with patch('builtins.input',side_effect=['/provider gemini','/compare a b question','/comparisons','/exit']),contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(app.main([]),0)
            saved=json.loads((root/'memory.json').read_text(encoding='utf-8'))
            self.assertEqual(saved['conversations'],[])
            self.assertEqual(saved['comparisons'][0]['question'],'question')

    def test_partial_response_rejected(self):
        provider=cmp.LocalProvider()
        for result in [{'done':False,'message':{'content':'partial'}},{'done':True,'done_reason':'length','message':{'content':'partial'}},{'done':True,'message':{'content':3}}]:
            with patch.object(provider,'_request',return_value=result), self.assertRaises(app.ProviderError):
                provider.generate([])

    def test_nonlocal_endpoint_rejected(self):
        with self.assertRaises(app.ProviderError):
            cmp.LocalProvider(base_url='https://example.com')._request('/api/tags')

if __name__=='__main__':
    unittest.main()
