import hashlib
import json
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from tomeris_desktop_v059 import DesktopService
from tomeris_restore_v059 import validate_memory_tags


class MemoryTagRestoreTests(unittest.TestCase):
    def test_valid_and_tolerated_legacy_shapes(self):
        for row in (None, {}, {'tags':None}, {'tags':'legacy'}, {'tags':['目標', '生活']}, {'tags':[]}):
            validate_memory_tags({'memories':[row]})
        validate_memory_tags({})

    def test_nontext_list_tags_rejected(self):
        for value in (123, None, {}, [], True):
            with self.assertRaises(ValueError):
                validate_memory_tags({'memories':[{'tags':['正常', value]}]})

    def test_verified_zip_invalid_tags_refused_and_original_preserved(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = DesktopService(root/'data', demo=True)
            try:
                service.store.add_memory('目標', '復元検証の目標', '正常')
                original = service.memory_path.read_bytes()
                archive = root/'valid.zip'
                service.export_backup(archive)
                with zipfile.ZipFile(archive) as src:
                    entries = {name:src.read(name) for name in src.namelist()}
                memory = json.loads(entries['tomeris_memory.json'])
                memory['memories'][0]['tags'] = ['正常', 1]
                raw = json.dumps(memory, ensure_ascii=False).encode('utf-8')
                entries['tomeris_memory.json'] = raw
                manifest = json.loads(entries['manifest.json'])
                for item in manifest['files']:
                    if item['name'] == 'tomeris_memory.json':
                        item.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
                entries['manifest.json'] = json.dumps(manifest).encode('utf-8')
                bad = root/'bad.zip'
                with zipfile.ZipFile(bad, 'w') as dst:
                    for name, value in entries.items():
                        dst.writestr(name, value)
                digest = hashlib.sha256(bad.read_bytes()).hexdigest()
                with self.assertRaises(ValueError):
                    service.inspect_backup(bad)
                with self.assertRaises(ValueError):
                    service.restore_backup(bad, root, digest)
                self.assertEqual([], list(root.glob('tomeris_restored_*')))
                self.assertEqual(original, service.memory_path.read_bytes())
                service.memory_path.write_bytes(raw)
                with self.assertRaises(ValueError):
                    service.export_backup(root/'invalid-export.zip')
                self.assertFalse((root/'invalid-export.zip').exists())
                self.assertEqual(raw, service.memory_path.read_bytes())
            finally:
                service.close()
