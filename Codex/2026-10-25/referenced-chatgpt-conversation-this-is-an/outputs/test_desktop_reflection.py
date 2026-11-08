from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import tomeris_plan_reflection as reflection
from tomeris_plans import today

class ReflectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.service=reflection.DesktopService(self.tmp.name,demo=True)
        self.service.save_plan('確認',10,[{'title':'実行する','minutes':5}],today())
        self.identifier=self.service.today_plan()['id']
        self.original={p.name:p.read_bytes() for p in Path(self.tmp.name).glob('*.json')}
        self.path=Path(self.tmp.name)/'plan_reflections.json'
    def tearDown(self):
        for name,data in self.original.items():
            self.assertEqual((Path(self.tmp.name)/name).read_bytes(),data)
        self.service.close(); self.tmp.cleanup()
    def test_read_save_restart_and_history(self):
        self.assertEqual(self.service.get_reflection(self.identifier)['text'],'')
        self.assertFalse(self.path.exists())
        self.service.save_reflection(self.identifier,'最初の一歩を進められた。',0)
        self.service.close(); self.service=reflection.DesktopService(self.tmp.name,demo=True)
        state=self.service.get_reflection(self.identifier)
        self.assertEqual(state['text'],'最初の一歩を進められた。')
        self.assertEqual(state['revision'],1)
        self.assertIn(state['text'],reflection.describe(self.service.plan_history()[0]))
    def test_edit_history_duplicate_and_conflict(self):
        self.service.save_reflection(self.identifier,'最初',0)
        before=self.path.read_bytes()
        self.service.save_reflection(self.identifier,'最初',1)
        self.assertEqual(before,self.path.read_bytes())
        self.service.save_reflection(self.identifier,'書き直し',1)
        self.assertEqual(len(self.service._reflections()['plans'][self.identifier]),2)
        with self.assertRaises(ValueError):
            self.service.save_reflection(self.identifier,'古い画面からの更新',1)
        self.assertEqual(self.service.get_reflection(self.identifier)['text'],'書き直し')
    def test_invalid_text_missing_plan_and_no_save(self):
        for text in ['', '  ', 'あ'*2001, None]:
            with self.assertRaises(ValueError):
                self.service.save_reflection(self.identifier,text,0)
        with self.assertRaises(ValueError):
            self.service.save_reflection('missing','内容',0)
        self.assertFalse(self.path.exists())
    def test_failure_keeps_saved_note(self):
        self.service.save_reflection(self.identifier,'元の文章',0)
        before=self.path.read_bytes()
        with patch.object(reflection.os,'replace',side_effect=OSError()),self.assertRaises(OSError):
            self.service.save_reflection(self.identifier,'新しい文章',1)
        self.assertEqual(before,self.path.read_bytes())
        self.assertEqual(list(Path(self.tmp.name).glob('plan_reflections_*.tmp')),[])
    def test_corrupt_file_never_overwritten(self):
        self.path.write_text('{broken')
        with self.assertRaises(ValueError):
            self.service.save_reflection(self.identifier,'内容',0)
        self.assertEqual(self.path.read_text(),'{broken')

if __name__=='__main__': unittest.main()
