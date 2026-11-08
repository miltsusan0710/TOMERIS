import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import tomeris_plans as plans

class PlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.service=plans.DesktopService(self.tmp.name,demo=True)
        self.service.models()
        self.path=Path(self.tmp.name)/'daily_plans.json'
        self.before=self.service.memory_path.read_bytes()
    def tearDown(self):
        self.assertEqual(self.before,self.service.memory_path.read_bytes())
        self.service.close(); self.tmp.cleanup()
    def test_review_and_revision_persistence(self):
        draft=self.service.draft_plan('読書',30,'qwen2.5:3b')
        self.assertFalse(self.path.exists())
        self.service.save_plan(**draft,expected_date=plans.today())
        self.service.save_plan('執筆',20,[{'title':'下書き','minutes':15}],plans.today())
        self.assertIn('下書き',self.service.view('today'))
        self.assertEqual(len(json.loads(self.path.read_text(encoding='utf-8'))['plans']),2)
        self.service.close()
        self.service=plans.DesktopService(self.tmp.name,demo=True)
        self.assertIn('下書き',self.service.view('today'))
    def test_day_change(self):
        with self.assertRaises(ValueError):
            self.service.save_plan('読書',10,[{'title':'読む','minutes':10}],'2000-01-01')
        self.assertFalse(self.path.exists())
        self.service.save_plan('読書',10,[{'title':'読む','minutes':10}],plans.today())
        with patch.object(plans,'today',return_value='2099-01-01'):
            self.assertIn('まだありません',self.service.view('today'))
    def test_reject_invalid_plans(self):
        for tasks in [[],[{'title':'読む','minutes':11}],[{'title':'','minutes':1}],
                      [{'title':'読む','minutes':True}],[{'title':'読む','minutes':0}],
                      [{'title':'読む','minutes':1}]*4]:
            with self.subTest(tasks=tasks),self.assertRaises(ValueError):
                self.service.save_plan('読書',10,tasks,plans.today())
        self.assertFalse(self.path.exists())
    def test_corrupt_file_preserved(self):
        self.path.write_text('{broken',encoding='utf-8')
        with self.assertRaises(ValueError):
            self.service.save_plan('読書',10,[{'title':'読む','minutes':10}],plans.today())
        self.assertEqual(self.path.read_text(),'{broken')
    def test_failed_replace_preserves_previous(self):
        args=('読書',10,[{'title':'読む','minutes':10}],plans.today())
        self.service.save_plan(*args)
        previous=self.path.read_bytes()
        with patch.object(plans.os,'replace',side_effect=OSError('test')),self.assertRaises(OSError):
            self.service.save_plan(*args)
        self.assertEqual(self.path.read_bytes(),previous)
        self.assertEqual(list(self.path.parent.glob('daily_plans_*.tmp')),[])
    def test_model_response_and_no_memory_in_request(self):
        self.service.demo=False
        result={'done':True,'message':{'content':json.dumps({'tasks':[{'title':'読む','minutes':10}]})}}
        with patch.object(plans.LocalProvider,'_request',return_value=result) as request:
            self.service.draft_plan('読書',10,'qwen2.5:3b')
            payload=request.call_args.kwargs['payload']
            self.assertEqual(len(payload['messages']),2)
            self.assertEqual(json.loads(payload['messages'][1]['content']),{'goal':'読書','available_minutes':10})
        self.assertFalse(self.path.exists())
        for response in [{'done':False}, {'done':True,'message':{'content':'invalid'}},
                         {'done':True,'message':{'content':'{"tasks":[{"title":"読む","minutes":100}]}'}}]:
            with patch.object(plans.LocalProvider,'_request',return_value=response),self.assertRaises(ValueError):
                self.service.draft_plan('読書',10,'qwen2.5:3b')
        self.assertFalse(self.path.exists())

if __name__=='__main__':
    unittest.main()
