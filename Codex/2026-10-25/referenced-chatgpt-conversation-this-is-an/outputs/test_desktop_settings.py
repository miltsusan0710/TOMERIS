from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
import tomeris_settings as settings

class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.service=settings.DesktopService(self.tmp.name,demo=True)
        self.service.models(); self.memory=self.service.memory_path.read_bytes()
        self.path=Path(self.tmp.name)/'desktop_settings.json'
    def tearDown(self):
        self.assertEqual(self.memory,self.service.memory_path.read_bytes())
        self.service.close(); self.tmp.cleanup()
    def test_explicit_save_and_restart(self):
        self.assertFalse(self.path.exists()); self.assertIsNone(self.service.startup_model)
        self.service.save_startup_model('qwen2.5:1.5b')
        self.service.close(); self.service=settings.DesktopService(self.tmp.name,demo=True)
        self.assertEqual(self.service.startup_model,'qwen2.5:1.5b')
    def test_invalid_model_not_saved(self):
        with self.assertRaises(ValueError): self.service.save_startup_model('missing-model')
        self.assertFalse(self.path.exists())
    def test_failed_save_preserves_previous(self):
        self.service.save_startup_model('qwen2.5:3b'); before=self.path.read_bytes()
        with patch.object(settings.os,'replace',side_effect=OSError()),self.assertRaises(OSError):
            self.service.save_startup_model('qwen2.5:1.5b')
        self.assertEqual(self.path.read_bytes(),before)
        self.assertEqual(self.service.startup_model,'qwen2.5:3b')
        self.assertEqual(list(Path(self.tmp.name).glob('desktop_settings_*.tmp')),[])
    def test_corrupt_settings_does_not_block_startup(self):
        self.service.close(); self.path.write_text('{broken')
        self.service=settings.DesktopService(self.tmp.name,demo=True)
        self.assertIsNone(self.service.startup_model); self.assertTrue(self.service.settings_notice)
        self.assertEqual(self.path.read_text(),'{broken')
    def test_missing_model_and_available_preference(self):
        self.assertEqual(settings.choose_startup_model('small',['large','small'],'large'),('small',''))
        model,notice=settings.choose_startup_model('missing',['large'],'small')
        self.assertEqual(model,'large'); self.assertIn('保存設定は変更していません',notice)
        self.assertEqual(settings.choose_startup_model('small',[],'large'),('large',''))

if __name__=='__main__': unittest.main()
