import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v045 import DesktopService
class PersonaTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.s.close)
 def test_default_restrained(self):
  self.assertIn('今回はジョークや皮肉を加えず',self.s.conversation_persona('こんにちは'))
 def test_humor_optional_and_not_consecutive(self):
  self.assertIn('入れなくてもよい',self.s.conversation_persona('少し雑談しよう'))
  for i in range(4):self.assertIn('今回はジョーク',self.s.conversation_persona('雑談しよう'))
  self.assertIn('入れなくてもよい',self.s.conversation_persona('雑談しよう'))
 def test_serious_overrides_casual(self):
  for text in ('不安なので雑談したい','地震のジョーク','困っているから冗談抜きで','お金の悩みを面白く話したい'):
   self.assertIn('今回はジョーク',self.s.conversation_persona(text))
 def test_local_chat_receives_persona(self):
  self.s.demo=False;self.s.model_names=['test']
  with patch('tomeris_capabilities.core.generate_checked_response',return_value='確認しました。') as gen:
   self.s.chat('雑談しよう','test')
  provider=gen.call_args.args[0];self.assertIn('落ち着きと機転',provider.style)
 def test_schedule_does_not_invoke_persona(self):
  with patch.object(self.s,'conversation_persona',side_effect=AssertionError('must not rewrite plans')):
   self.assertIn('計画はありません',self.s.chat('今日の予定は？','test'))
 def test_original_persona_and_memory_not_modified(self):
  before=self.s.memory_path.read_bytes();self.s.conversation_persona('休憩しよう');self.assertEqual(before,self.s.memory_path.read_bytes())
