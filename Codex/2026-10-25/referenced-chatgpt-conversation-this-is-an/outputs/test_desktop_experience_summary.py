import tempfile
import unittest
from pathlib import Path
from tomeris_adaptive_collection import DesktopService
from tomeris_experience_summary import summarize, format_summary

class ExperienceSummaryTests(unittest.TestCase):
    def test_legacy_not_inferred_and_history_unchanged(self):
        rows = [dict(action='exact', success=False),
                dict(action='exact', success=False, outcome='retrieval_error'),
                dict(action='normalized', success=True, outcome='evidence')]
        original = [dict(row) for row in rows]
        counts = summarize(rows)
        self.assertEqual(sum(counts.values()), 3)
        self.assertEqual(counts['legacy'], 1)
        self.assertEqual(counts['no_evidence'], 0)
        self.assertEqual(rows, original)
        self.assertIn('旧形式（理由未記録）：1件', format_summary(counts))

    def test_state_reports_persisted_counts_without_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            service = DesktopService(Path(folder), demo=True)
            try:
                service.remember_attempts([dict(action='exact', success=False, outcome='no_candidate'),
                    dict(action='normalized', success=False, outcome='no_evidence')])
                before = service.adaptive_path.read_bytes()
                state = service.collection_state()
                self.assertEqual(state['adaptive_outcomes']['no_candidate'], 1)
                self.assertEqual(state['adaptive_outcomes']['no_evidence'], 1)
                self.assertEqual(state['adaptive_attempts'], 2)
                self.assertEqual(service.adaptive_path.read_bytes(), before)
            finally:
                service.close()
