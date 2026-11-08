"""Integration checks against the actual desktop shortcut target, using temp data."""
import importlib
import re
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from test_desktop_source_backup import ROW


def latest_service():
    entry = (Path(__file__).parent / 'tomeris_desktop.py').read_text(encoding='utf-8-sig')
    module = re.search(r'from (tomeris_desktop_v\d+) import main', entry)[1]
    return importlib.import_module(module).DesktopService


class LatestRestoreTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.cls = latest_service()
        self.s = self.cls(self.root / 'original', demo=True)
        self.addCleanup(self.s.close)
        self.s.catalogue.save([dict(ROW)], True)
        self.s.save_collection_topics(['論理的思考', '情報リテラシー'])
        self.s.research_journal.append('テスト調査', '選択設定：自動', [dict(title=ROW['title'], url=ROW['url'])])
        self.s.chat('前は100個中10個、後は40個中8個', 'unused')
        self.s.source_checks[ROW['url']] = '再取得成功（テスト用の一時状態）'
        self.s.research_source_snapshot = dict(question='一時調査', time='test', sources=[])
        self.before = {p.name:p.read_bytes() for p in self.s.data_dir.glob('*.json')}
        self.archive = self.root / 'backup.zip'
        self.s.export_backup(self.archive)
        self.checked = self.s.inspect_backup(self.archive)
        self.parent = self.root / 'restores'
        self.parent.mkdir()
        self.sentinel = self.parent / 'existing.txt'
        self.sentinel.write_text('KEEP', encoding='utf-8')

    def unchanged(self):
        self.assertEqual(self.before, {p.name:p.read_bytes() for p in self.s.data_dir.glob('*.json')})
        self.assertEqual('KEEP', self.sentinel.read_text(encoding='utf-8'))

    def test_roundtrip_preserves_data_but_not_current_confirmation(self):
        folder = Path(self.s.restore_backup(self.archive, self.parent, self.checked['digest']))
        for name in self.checked['files']:
            self.assertEqual(self.before[name], (folder/name).read_bytes())
        restored = self.cls(folder, demo=True)
        try:
            self.assertEqual(self.s.collection_topics, restored.collection_topics)
            self.assertFalse(restored.auto_sources_enabled)
            self.assertEqual(self.s.research_journal.read(), restored.research_journal.read())
            self.assertEqual(self.s.catalogue.rows, restored.catalogue.rows)
            self.assertEqual({}, restored.source_checks)
            self.assertIsNone(restored.research_source_snapshot)
            self.assertIsNone(restored.ratio_snapshot)
            self.assertIn('未実施', restored.source_records()['rows'][0]['check'])
        finally:
            restored.close()
        self.unchanged()

    def test_changed_payload_rejected_before_folder_creation(self):
        corrupted = self.root/'corrupted.zip'
        with zipfile.ZipFile(self.archive) as src, zipfile.ZipFile(corrupted, 'w') as dst:
            for name in src.namelist():
                data = src.read(name)
                if name == 'research_sources.json':
                    data += b' '
                dst.writestr(name, data)
        with self.assertRaises(ValueError):
            self.s.restore_backup(corrupted, self.parent, self.checked['digest'])
        self.assertEqual([self.sentinel], list(self.parent.iterdir()))
        self.unchanged()

    def test_partial_write_failure_cleans_only_new_restore(self):
        original_open = Path.open
        def failing_open(path, mode='r', *args, **kwargs):
            if path.name == 'research_sources.json' and mode == 'xb':
                raise OSError('simulated disk failure')
            return original_open(path, mode, *args, **kwargs)
        with patch.object(Path, 'open', failing_open):
            with self.assertRaises(OSError):
                self.s.restore_backup(self.archive, self.parent, self.checked['digest'])
        self.assertEqual([self.sentinel], list(self.parent.iterdir()))
        self.unchanged()

    def test_old_optional_files_absent_and_wrong_digest(self):
        with self.assertRaises(ValueError):
            self.s.restore_backup(self.archive, self.parent, '0'*64)
        self.assertEqual([self.sentinel], list(self.parent.iterdir()))
        minimal = self.cls(self.root/'minimal', demo=True)
        try:
            old = self.root/'minimal.zip'
            minimal.export_backup(old)
            info = minimal.inspect_backup(old)
            folder = Path(minimal.restore_backup(old, self.parent, info['digest']))
            self.assertTrue((folder/'tomeris_memory.json').exists())
            self.assertNotIn('auto_topics.json', info['files'])
        finally:
            minimal.close()
        self.unchanged()
