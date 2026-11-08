import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import tomeris_v06 as app


class SafetyTests(unittest.TestCase):
    def test_pc_command_never_calls_ai(self):
        with patch("builtins.input", side_effect=["/pc", "/exit"]), patch.object(app, "chat") as chat:
            with contextlib.redirect_stdout(io.StringIO()):
                app.main(["--model", "test"])
            chat.assert_not_called()

    def test_info_not_added_to_history(self):
        with patch("builtins.input", side_effect=["/pc", "hello", "/exit"]), patch.object(app, "chat", return_value="ok") as chat:
            with contextlib.redirect_stdout(io.StringIO()):
                app.main(["--model", "test"])
            self.assertEqual(chat.call_args.args[1], [{"role": "user", "content": "hello"}])

    def test_existing_files_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            previous = os.getcwd()
            try:
                os.chdir(folder)
                for name in ("tomeris_memory.json", "tomeris_v04.py", "tomeris_v051.py"):
                    Path(name).write_bytes(b"existing-content")
                before = {p.name: p.read_bytes() for p in Path(folder).iterdir()}
                with contextlib.redirect_stdout(io.StringIO()):
                    app.main(["--pc-info"])
                self.assertEqual(before, {p.name: p.read_bytes() for p in Path(folder).iterdir()})
            finally:
                os.chdir(previous)

    def test_live_windows_info(self):
        info = app.pc_info()
        self.assertGreater(info["cpu"]["logical_processors"], 0)
        self.assertGreater(info["system_disk"]["total_bytes"], 0)
        if app.sys.platform == "win32":
            self.assertGreater(info["memory"]["total_bytes"], 0)
        self.assertNotIn("hostname", json.dumps(info))

    def test_failure_and_unknown_command_do_not_execute(self):
        with patch("builtins.input", side_effect=["/run anything", "hi", "/exit"]), patch.object(app, "chat", side_effect=OSError) as chat:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(app.main(["--model", "test"]), 0)
            self.assertEqual(chat.call_count, 1)


if __name__ == "__main__":
    unittest.main()
