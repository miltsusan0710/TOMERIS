import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_source_check_state import DesktopService
from tomeris_page_reader import PageError
from test_desktop_source_backup import ROW


class SourceCheckStateTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.s = DesktopService(Path(tmp.name), demo=True)
        self.addCleanup(self.s.close)
        self.s.catalogue.save([dict(ROW)], True)
        self.s.demo = False

    def row(self):
        return self.s.source_records()['rows'][0]

    def success(self):
        row = self.row()
        with patch('tomeris_source_management.fetch_page', return_value=dict(url=ROW['url'], text='取得本文')):
            self.s.check_source(row['url'], row['revision'])

    def test_normal_failure_replaces_success_preserving_saved_evidence(self):
        before = self.s.catalogue.path.read_bytes()
        self.success()
        row = self.row()
        with patch('tomeris_source_management.fetch_page', side_effect=PageError('接続不可')):
            self.s.check_source(row['url'], row['revision'])
        self.assertIn('再取得失敗', self.row()['check'])
        self.assertNotIn('再取得成功', self.row()['check'])
        self.assertEqual(before, self.s.catalogue.path.read_bytes())

    def test_unexpected_failure_cannot_retain_success(self):
        self.success()
        row = self.row()
        with patch('tomeris_source_management.fetch_page', side_effect=RuntimeError('private diagnostic')):
            with self.assertRaises(RuntimeError):
                self.s.check_source(row['url'], row['revision'])
        status = self.row()['check']
        self.assertIn('再取得失敗', status)
        self.assertNotIn('private diagnostic', status)
        self.assertNotIn('再取得成功', status)

    def test_updated_source_invalidates_old_status(self):
        self.success()
        self.s.catalogue.save([dict(ROW, excerpt='別の保存本文')], True)
        self.assertIn('未実施', self.row()['check'])
        self.assertNotIn(ROW['url'], self.s.source_checks)

    def test_demo_does_not_reuse_real_success(self):
        self.success()
        self.s.demo = True
        row = self.row()
        with patch('tomeris_source_management.fetch_page', side_effect=AssertionError('no fetch')):
            self.s.check_source(row['url'], row['revision'])
        self.assertIn('実行していません', self.row()['check'])
        self.assertNotIn('再取得成功', self.row()['check'])

    def test_removal_clears_revision(self):
        self.success()
        row = self.row()
        self.s.remove_source(row['url'], row['revision'])
        self.assertNotIn(row['url'], self.s.source_check_revisions)

    def test_timestamp_is_check_time_not_saved_time(self):
        self.success()
        row = self.row()
        self.assertEqual(ROW['retrieved'], row['retrieved'])
        self.assertIn('JST', row['check'])
        self.assertIn('正確さは未検証', row['check'])

    def test_panel_failure_replaces_cached_success(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from tomeris_sources_ui_v056 import SourcesPanel
        row = dict(url=ROW['url'], revision='old', check='再取得成功')
        panel = object.__new__(SourcesPanel)
        panel.selected = lambda: row
        panel.app = SimpleNamespace(service=SimpleNamespace(check_source=Mock(side_effect=RuntimeError('private'))))
        panel.message = Mock()
        panel.show_selected = Mock()
        panel.run = lambda operation, callback: callback(operation())
        panel.check_selected()
        self.assertIn('再取得失敗', row['check'])
        self.assertNotIn('再取得成功', row['check'])
        panel.show_selected.assert_called_once()
