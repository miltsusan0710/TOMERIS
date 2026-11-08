import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import tomeris_v082 as app


class V06Tests(unittest.TestCase):
    def test_live_windows_metrics(self):
        info = app.pc_info()
        self.assertGreater(info['cpu']['logical_processors'], 0)
        self.assertGreater(info['memory']['total_bytes'], 0)
        self.assertGreater(info['system_disk']['total_bytes'], 0)
        self.assertNotIn('hostname', json.dumps(info))

    def test_one_shot_never_opens_memory_or_ai(self):
        with patch.object(app, 'MemoryStore', side_effect=AssertionError), patch.object(app, 'OllamaProvider', side_effect=AssertionError):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(app.main(['--pc-info']), 0)

    def test_import_is_exact_and_never_overwrites(self):
        with TemporaryDirectory() as folder:
            source = Path(folder)/'tomeris_memory.json'
            target = Path(folder)/'tomeris_memory_v06.json'
            raw = b'{"version":3,"memories":[]}'
            source.write_bytes(raw)
            app.import_memory(source, target)
            self.assertEqual(target.read_bytes(), raw)
            with self.assertRaises(FileExistsError):
                app.import_memory(source, target)
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(target.read_bytes(), raw)

    def test_invalid_import_creates_no_target(self):
        with TemporaryDirectory() as folder:
            source, target = Path(folder)/'old.json', Path(folder)/'new.json'
            source.write_text('broken', encoding='utf-8')
            with self.assertRaises(ValueError):
                app.import_memory(source, target)
            self.assertFalse(target.exists())

    def test_pc_result_not_stored_or_forwarded(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source = root/'tomeris_memory.json'
            source.write_bytes(b'{"memories":[]}')
            baseline = source.read_bytes()
            with patch.object(app, 'MEMORY_FILE', root/'tomeris_memory_v06.json'), patch.object(app, 'KNOWLEDGE_DIR', root/'knowledge'), patch.object(app, 'CORE_FILE', root/'core.md'), patch.object(app.OllamaProvider, 'check', return_value=(False,'offline')), patch.object(app.OllamaProvider, 'generate', return_value='hello') as generate, patch.object(app, 'pc_info', return_value={'unique_pc_marker':123}):
                with patch('builtins.input', side_effect=['/pc', '/pc delete', 'こんにちは', '/exit']), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(app.main([]), 0)
            saved = (root/'tomeris_memory_v06.json').read_text(encoding='utf-8')
            self.assertNotIn('unique_pc_marker', saved)
            self.assertNotIn('/pc', saved)
            self.assertNotIn('unique_pc_marker', str(generate.call_args))
            self.assertEqual(generate.call_count, 1)
            self.assertEqual(source.read_bytes(), baseline)


if __name__ == '__main__':
    unittest.main()
