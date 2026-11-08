import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import tomeris_diagnose as diag

class DiagnosisTests(unittest.TestCase):
    def test_read_only_store_and_conditions(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)/'memory.json'
            raw=json.dumps({'memories':[{'text':'UNIQUE_MEMORY','importance':3}], 'growth_log':[], 'conversations':[{'user':'UNIQUE_USER','tomeris':'UNIQUE_ASSISTANT'}]}).encode()
            path.write_bytes(raw)
            store=diag.ReadOnlyStore(path,Path(folder)/'missing_knowledge')
            with patch.object(diag.app,'read_core',return_value='core'):
                cases=diag.profiles(diag.QUESTION,store)
            self.assertNotIn('UNIQUE_USER',str(cases[0]))
            self.assertNotIn('UNIQUE_USER',str(cases[1]))
            self.assertIn('UNIQUE_USER',str(cases[2]))
            self.assertEqual(path.read_bytes(),raw)
            self.assertFalse((Path(folder)/'missing_knowledge').exists())
            with self.assertRaises(RuntimeError):
                store.save()
    def test_seed_does_not_mutate_payload(self):
        provider=diag.DiagnosticProvider()
        payload={'options':{'temperature':0.3}}
        with patch.object(diag.LocalProvider,'_request',return_value={}) as request:
            provider._request('/api/chat',payload)
        self.assertNotIn('seed',payload['options'])
        self.assertEqual(request.call_args.kwargs['payload']['options']['seed'],42)
    def test_three_calls_no_retry_on_failure(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)/'memory.json'
            raw=b'{"memories":[],"growth_log":[],"conversations":[]}'
            path.write_bytes(raw)
            with patch.object(diag,'list_models',return_value={'qwen2.5:3b':{}}),patch.object(diag.DiagnosticProvider,'generate',side_effect=[diag.ProviderError('offline'),'answer B','answer C']) as generate,contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(diag.main(['--memory',str(path)]),1)
            self.assertEqual(generate.call_count,3)
            self.assertEqual(path.read_bytes(),raw)
if __name__=='__main__':
    unittest.main()
