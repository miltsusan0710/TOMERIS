import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_analysis_style import DesktopService, GUIDANCE


class AnalysisStyleTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.s = DesktopService(Path(tmp.name), demo=True)
        self.addCleanup(self.s.close)

    def test_analysis_specific_and_humor_suppressed(self):
        for question in ('広告費を倍にすべき？', 'この手順のおかげと断定できる？',
                         '雑談だけど、遅刻の原因は？'):
            style = self.s.conversation_persona(question)
            self.assertIn(GUIDANCE, style)
            self.assertIn('今回はジョークや皮肉を加えず', style)

    def test_ordinary_chat_keeps_short_style(self):
        self.assertNotIn(GUIDANCE, self.s.conversation_persona('こんにちは'))
        self.assertNotIn(GUIDANCE, self.s.conversation_persona('休憩して雑談しよう'))

    def test_passes_to_local_provider(self):
        self.s.demo = False
        self.s.model_names = ['test']
        with patch('tomeris_capabilities.core.generate_checked_response', return_value='未確認です。') as gen:
            self.s.chat('手順の効果があると断定できる？', 'test')
        self.assertIn(GUIDANCE, gen.call_args.args[0].style)

    def test_deterministic_answers_bypass_style(self):
        with patch.object(self.s, 'conversation_persona', side_effect=AssertionError('unexpected generation')):
            self.assertIn('計画はありません', self.s.chat('今日の予定は？', 'test'))
            self.assertIn('結果：4', self.s.chat('計算: 2+2', 'test'))

    def test_no_persistent_change_from_style(self):
        before = self.s.memory_path.read_bytes()
        self.s.conversation_persona('原因は？')
        self.assertEqual(before, self.s.memory_path.read_bytes())
