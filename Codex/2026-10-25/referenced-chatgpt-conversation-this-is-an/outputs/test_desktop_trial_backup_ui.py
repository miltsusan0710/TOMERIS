import unittest,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from tomeris_trial_backup_ui import open_backup

class BackupUiTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.records=self.root/'research_trials';self.records.mkdir();(self.records/'record.json').write_text('{}')
  self.jobs=[];self.app=SimpleNamespace(root=None,busy=False,closing=False,service=SimpleNamespace(data_dir=self.root),submit=lambda *args:self.jobs.append(args))
 def run_job(self):
  callback,outcome=self.jobs.pop()[1]()
  with patch('tkinter.messagebox.showinfo') as info,patch('tkinter.messagebox.showerror') as error:callback(outcome)
  return info,error
 def test_save_then_inspect(self):
  path=self.root/'saved.zip'
  with patch('tkinter.filedialog.asksaveasfilename',return_value=str(path)):open_backup(self.app)
  info,error=self.run_job();self.assertTrue(path.exists());info.assert_called_once();error.assert_not_called()
  with patch('tkinter.filedialog.askopenfilename',return_value=str(path)):open_backup(self.app,True)
  info,error=self.run_job();self.assertIn('1ファイル',info.call_args.args[1]);error.assert_not_called()
  self.assertEqual((self.records/'record.json').read_text(),'{}')
 def test_existing_file_is_not_overwritten(self):
  path=self.root/'saved.zip';path.write_bytes(b'keep')
  with patch('tkinter.filedialog.asksaveasfilename',return_value=str(path)):open_backup(self.app)
  info,error=self.run_job();error.assert_called_once();info.assert_not_called();self.assertEqual(path.read_bytes(),b'keep')
 def test_cancel_busy_and_late_close(self):
  with patch('tkinter.filedialog.askopenfilename',return_value=''):open_backup(self.app,True)
  self.assertFalse(self.jobs);self.app.busy=True;open_backup(self.app);self.assertFalse(self.jobs)
  self.app.busy=False
  with patch('tkinter.filedialog.asksaveasfilename',return_value=str(self.root/'new.zip')):open_backup(self.app)
  callback,outcome=self.jobs.pop()[1]();self.app.closing=True
  with patch('tkinter.messagebox.showinfo') as info:callback(outcome);info.assert_not_called()
 def test_invalid_archive_shown_as_error(self):
  path=self.root/'invalid.zip';path.write_bytes(b'notzip')
  with patch('tkinter.filedialog.askopenfilename',return_value=str(path)):open_backup(self.app,True)
  info,error=self.run_job();error.assert_called_once();info.assert_not_called()
