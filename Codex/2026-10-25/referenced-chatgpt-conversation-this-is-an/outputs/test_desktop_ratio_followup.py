import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_ratio_followup import DesktopService


class RatioFollowupTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.s = DesktopService(Path(tmp.name), demo=True)
        self.addCleanup(self.s.close)

    def seed(self):
        self.s.chat('前は100個中10個、後は40個中8個', 'unused')

    def test_repeated_followups_cannot_reverse_result(self):
        self.seed()
        with patch('tomeris_capabilities.core.generate_checked_response', side_effect=AssertionError('no model')):
            for q in ('どういうこと？', 'じゃあ改善してない？', '改善したの？'):
                answer = self.s.web_chat(q, 'unused', automatic=True)
                self.assertIn('割合の増加は改善ではありません', answer)
                self.assertIn('10.00ポイントの増加', answer)
                self.assertIn('原因や施策の効果', answer)

    def test_new_comparison_replaces_old(self):
        self.seed()
        self.s.chat('前は50件中5件、後は200件中12件', 'unused')
        answer = self.s.chat('つまり？', 'unused')
        self.assertIn('4.00ポイントの減少', answer)
        self.assertNotIn('20.00％', answer)

    def test_clear_on_topic_cancel_greeting_and_invalid_data(self):
        for q in ('別の話', 'キャンセル', 'こんにちは', '前は0個中0個、後は1個中0個'):
            self.seed()
            self.s.chat(q, 'unused')
            self.assertIsNone(self.s.ratio_snapshot)

    def test_unrelated_input_and_failed_generation_clear(self):
        self.seed()
        self.s.demo = False
        self.s.model_names = ['test']
        with patch('tomeris_capabilities.core.generate_checked_response', side_effect=RuntimeError('offline')):
            with self.assertRaises(RuntimeError):
                self.s.chat('猫の話をして', 'test')
        self.assertIsNone(self.s.ratio_snapshot)

    def test_equal_ratio_not_improvement(self):
        self.s.chat('前は2人中1人、後は4人中2人', 'unused')
        self.assertIn('割合で見る限り変化はありません', self.s.chat('改善した？', 'unused'))

    def test_context_not_restored_from_history(self):
        self.seed()
        folder = self.s.data_dir
        self.s.close()
        other = DesktopService(folder, demo=True)
        try:
            self.assertIsNone(other.ratio_snapshot)
        finally:
            other.close()
