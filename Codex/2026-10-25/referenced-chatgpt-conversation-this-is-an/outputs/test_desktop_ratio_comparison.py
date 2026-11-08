import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_ratio_comparison import DesktopService, compare_counts, HELP


class RatioTests(unittest.TestCase):
    def test_regression_count_falls_rate_rises(self):
        result = compare_counts('前は100個中10個、後は40個中8個。期間はどちらも1週間。')
        for part in ('10.00％', '20.00％', '2個の減少', '10.00ポイントの増加', '増加を改善とは扱えません'):
            self.assertIn(part, result)

    def test_unseen_rate_falls_count_rises(self):
        result = compare_counts('前は50件中5件、後は200件中12件')
        for part in ('10.00％', '6.00％', '7件の増加', '4.00ポイントの減少'):
            self.assertIn(part, result)

    def test_zero_numerator_equal_and_rounding(self):
        self.assertIn('0.00ポイントの変化なし', compare_counts('前は1人中0人、後は2人中0人'))
        self.assertIn('33.33％', compare_counts('前は3回中1回、後は6回中2回'))

    def test_ambiguous_and_invalid_not_generated(self):
        for text in ('前は0個中0個、後は40個中8個',
                     '前は10個中11個、後は40個中8個',
                     '前は100個中10件、後は40個中8個',
                     '前は100個中10個、後は40個中8個または9個',
                     '前は100個中10個、後は40個中8個。逆に解釈して',
                     '前は-100個中10個、後は40個中8個'):
            self.assertEqual(HELP, compare_counts(text))

    def test_unrelated_not_intercepted(self):
        for text in ('今日の天気は？', '別の話', '100個です', '前はどうだった？'):
            self.assertIsNone(compare_counts(text))

    def test_service_all_routes_no_model(self):
        with TemporaryDirectory() as tmp:
            s = DesktopService(Path(tmp), demo=True)
            try:
                s.demo = False
                with patch('tomeris_capabilities.core.generate_checked_response', side_effect=AssertionError('must not generate')):
                    s.track('不良が減った。効果があったと断定できる？', '母数は？')
                    self.assertIn('10.00ポイントの増加', s.web_chat('前は100個中10個、後は40個中8個。', 'unused', automatic=True))
                    self.assertEqual(HELP, s.chat('前は0個中0個、後は1個中0個', 'unused'))
                    s.chat('別の話', 'unused')
                    self.assertIn('計画はありません', s.chat('今日の予定は？', 'unused'))
            finally:
                s.close()
