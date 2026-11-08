import hashlib
import json
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from tomeris_desktop_v058 import DesktopService
from tomeris_plans import today


class RestorePlanRowsTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.s = DesktopService(self.root/'data', demo=True)
        self.addCleanup(self.s.close)
        self.s.save_plan('確認', 10, [dict(title='読む', minutes=5)], today())
        self.path = self.root/'valid.zip'
        self.s.export_backup(self.path)
        with zipfile.ZipFile(self.path) as archive:
            self.contents = {name:archive.read(name) for name in archive.namelist()}

    def changed(self, rows):
        data = dict(self.contents)
        raw = json.dumps(dict(version=1, plans=rows), ensure_ascii=False).encode('utf-8')
        data['daily_plans.json'] = raw
        manifest = json.loads(data['manifest.json'])
        for item in manifest['files']:
            if item['name'] == 'daily_plans.json':
                item.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        data['manifest.json'] = json.dumps(manifest).encode('utf-8')
        path = self.root/'changed.zip'
        with zipfile.ZipFile(path, 'w') as archive:
            for name, value in data.items():
                archive.writestr(name, value)
        return path

    def test_invalid_rows_rejected_even_with_valid_hashes(self):
        good = dict(date=today(), goal='確認', budget=10, tasks=[dict(title='読む', minutes=5)])
        for row in (None, dict(good, date=123), dict(good, goal=''), dict(good, budget=True),
                    dict(good, tasks=[]), dict(good, tasks=[dict(title='読む', minutes=11)]),
                    dict(good, tasks=[dict(title='読む', minutes='5')])):
            with self.subTest(row=row):
                path = self.changed([row])
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                with self.assertRaises(ValueError):
                    self.s.inspect_backup(path)
                with self.assertRaises(ValueError):
                    self.s.restore_backup(path, self.root, digest)
                self.assertEqual([], list(self.root.glob('tomeris_restored_*')))

    def test_old_rows_without_approval_and_extra_fields_preserved(self):
        rows = [dict(date='2020-01-01', goal='確認', budget=10, tasks=[dict(title='読む', minutes=5)], legacy_note='保持')]
        path = self.changed(rows)
        info = self.s.inspect_backup(path)
        restored = Path(self.s.restore_backup(path, self.root, info['digest']))
        self.assertEqual(rows, json.loads((restored/'daily_plans.json').read_text(encoding='utf-8'))['plans'])

    def test_empty_plans_supported(self):
        self.assertEqual(0, self.s.inspect_backup(self.changed([]))['counts']['plans'])

    def test_export_rejects_bad_plan_without_changing_original(self):
        source = self.s.data_dir/'daily_plans.json'
        raw = b'{"version":1,"plans":[null]}'
        source.write_bytes(raw)
        destination = self.root/'bad-export.zip'
        with self.assertRaises(ValueError):
            self.s.export_backup(destination)
        self.assertFalse(destination.exists())
        self.assertEqual(raw, source.read_bytes())
