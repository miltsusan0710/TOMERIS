import contextlib
import io
import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, MagicMock, patch
from urllib.error import HTTPError
import tomeris_gemini_v07 as gem
import tomeris_v082 as app

class GeminiTests(unittest.TestCase):
    def provider(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY':'test-secret'}):
            return gem.GeminiProvider()

    def response(self, text='hello', finish='STOP'):
        return json.dumps({'candidates':[{'finishReason':finish,'content':{'parts':[{'text':text}]}}]}).encode()

    def test_no_key_never_sends(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(gem,'build_opener') as network:
            provider=gem.GeminiProvider()
            with self.assertRaises(app.ProviderError):
                provider.generate([{'role':'user','content':'hi'}])
            network.assert_not_called()

    def test_cancel_never_sends(self):
        provider=self.provider()
        with patch('builtins.input',return_value='no'), patch.object(gem,'build_opener') as network, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(app.ProviderError):
                provider.generate([{'role':'user','content':'hi'}])
            network.assert_not_called()

    def test_exact_payload_no_memory_redirects_and_key_header(self):
        provider=self.provider()
        opener=MagicMock()
        opener.open.return_value.__enter__.return_value.read.return_value=self.response('hello test-secret')
        out=io.StringIO()
        with patch('builtins.input',return_value='yes'), patch.object(gem,'build_opener',return_value=opener), contextlib.redirect_stdout(out):
            result=provider.generate([{'role':'system','content':'PRIVATE_MEMORY'}, {'role':'user','content':'OLD_PRIVATE'}, {'role':'user','content':'current question'}])
        request=opener.open.call_args.args[0]
        payload=json.loads(request.data)
        self.assertEqual(payload['contents'],[{'role':'user','parts':[{'text':'current question'}]}])
        self.assertNotIn('PRIVATE',request.data.decode())
        self.assertNotIn('test-secret',request.full_url)
        self.assertNotIn('test-secret',out.getvalue())
        self.assertNotIn('test-secret',result)
        self.assertEqual(request.get_header('X-goog-api-key'),'test-secret')
        self.assertIsNone(gem.NoRedirect().redirect_request(None,None,302,'',{},'https://example.com'))

    def test_http_error_redacted(self):
        opener=MagicMock()
        opener.open.side_effect=HTTPError('https://host/test-secret',429,'test-secret',{},io.BytesIO(b'test-secret'))
        with patch('builtins.input',return_value='yes'), patch.object(gem,'build_opener',return_value=opener), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(app.ProviderError) as caught:
                self.provider().generate([{'role':'user','content':'hi'}])
        self.assertIn('429',str(caught.exception))
        self.assertNotIn('test-secret',str(caught.exception))
        self.assertEqual(opener.open.call_count,1)

    def test_malformed_and_blocked_responses(self):
        for raw in (b'bad', b'{}', b'[]', self.response(finish='MAX_TOKENS')):
            opener=MagicMock()
            opener.open.return_value.__enter__.return_value.read.return_value=raw
            with patch('builtins.input',return_value='yes'), patch.object(gem,'build_opener',return_value=opener), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(app.ProviderError):
                    self.provider().generate([{'role':'user','content':'hi'}])

    def test_cloud_does_not_read_store_or_retry(self):
        provider=Mock(cloud=True)
        provider.generate.return_value='PCのファイル削除を実行しました。'
        store=Mock()
        with patch.object(app,'build_messages',side_effect=AssertionError):
            answer=app.generate_checked_response(provider,store,'整理するコツは？')
        self.assertIn('未実行',answer)
        self.assertEqual(provider.generate.call_args.args[0],[{'role':'user','content':'整理するコツは？'}])
        store.build_context.assert_not_called()
        provider.generate.reset_mock()
        app.generate_checked_response(provider,store,'PC操作機能のリスクを3つ挙げて')
        self.assertEqual(provider.generate.call_count,1)

    def test_switch_cancel_and_pc_dont_persist_or_call_cloud(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            with patch.object(app,'MEMORY_FILE',root/'memory.json'), patch.object(app,'KNOWLEDGE_DIR',root/'knowledge'), patch.object(app.OllamaProvider,'check',return_value=(True,'local')), patch.object(gem,'build_opener') as network, patch.dict(os.environ,{'GEMINI_API_KEY':'test-secret'}):
                with patch('builtins.input',side_effect=['/provider gemini','/pc','question','no','/provider ollama','/exit']), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(app.main([]),0)
                network.assert_not_called()
            saved=(root/'memory.json').read_text(encoding='utf-8')
            self.assertNotIn('test-secret',saved)
            self.assertEqual(json.loads(saved)['conversations'],[])

    def test_hidden_key_not_saved_or_printed(self):
        provider=self.provider()
        out=io.StringIO()
        with patch.object(gem.getpass,'getpass',return_value='new-secret'), contextlib.redirect_stdout(out):
            self.assertTrue(provider.enter_key())
        self.assertNotIn('new-secret',out.getvalue())
        self.assertTrue(provider.check()[0])

    def test_invalid_model(self):
        with self.assertRaises(app.ProviderError):
            gem.GeminiProvider('https://other-host/')

if __name__=='__main__':
    unittest.main()

