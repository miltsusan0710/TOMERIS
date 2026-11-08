import unittest
from pathlib import Path
from unittest.mock import patch
from tomeris_composer_v085 import answer_image_bytes,Composer
from types import SimpleNamespace

class ComposerTests(unittest.TestCase):
 def test_image_temp_removed_on_failure(self):
  paths=[]
  def fail(path,*args):
   paths.append(Path(path));self.assertEqual(Path(path).read_bytes(),b'png');raise ValueError('vision failed')
  with patch('tomeris_composer_v085.image_answer',side_effect=fail):
   with self.assertRaises(ValueError):answer_image_bytes(b'png','質問','model')
  self.assertFalse(paths[0].exists())
 def test_busy_does_not_send_or_clear_attachment(self):
  composer=Composer.__new__(Composer);composer.data=b'image';composer.app=SimpleNamespace(busy=True,closing=False)
  self.assertTrue(composer.send_image());self.assertEqual(composer.data,b'image')
 def test_no_attachment_uses_text_send(self):
  composer=Composer.__new__(Composer);composer.data=None
  self.assertFalse(composer.send_image())
