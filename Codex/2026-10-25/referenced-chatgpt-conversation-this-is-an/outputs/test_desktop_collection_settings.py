import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v048 import DesktopService
from tomeris_backup_v043 import DesktopService as OldBackup
class CollectionSettingsTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'data';self.s=DesktopService(self.path,demo=True);self.addCleanup(self.s.close)
 def reopen(self):
  self.s.close();other=DesktopService(self.path,demo=True);self.s=other;self.addCleanup(other.close);return other
 def test_stop_and_resume_survive_restart(self):
  self.s.chat('自動資料収集を停止','unused');self.assertFalse(self.reopen().auto_sources_enabled)
  self.s.chat('自動資料収集を再開','unused');self.assertTrue(self.reopen().auto_sources_enabled)
 def test_corrupt_stops_and_preserves(self):
  p=self.s.auto_settings_path;p.write_bytes(b'{oops');s=self.reopen();self.assertFalse(s.auto_sources_enabled)
  self.assertIn('失敗',s.chat('自動資料収集を再開','unused'));self.assertEqual(p.read_bytes(),b'{oops')
 def test_failed_save_stops_now_but_reports_failure(self):
  with patch('tomeris_collection_settings.os.replace',side_effect=OSError('test')):
   answer=self.s.chat('自動資料収集を停止','unused')
  self.assertFalse(self.s.auto_sources_enabled);self.assertIn('保存に失敗',answer)
 def test_bad_boolean_rejected(self):
  self.s.auto_settings_path.write_text('{"version":1,"enabled":"false"}',encoding='utf-8');self.assertFalse(self.reopen().auto_sources_enabled)
 def test_backup_restore_and_legacy(self):
  self.s.set_auto_collection(False);dest=Path(self.tmp.name)/'new.zip';self.s.export_backup(dest)
  check=self.s.inspect_backup(dest);self.assertIs(check['counts']['auto_collection_enabled'],False)
  folder=Path(self.s.restore_backup(dest,Path(self.tmp.name),check['digest']))
  restored=DesktopService(folder,demo=True);self.addCleanup(restored.close);self.assertFalse(restored.auto_sources_enabled)
  old=Path(self.tmp.name)/'old.zip';OldBackup.export_backup(self.s,old);self.assertNotIn('auto_collection.json',self.s.inspect_backup(old)['files'])
 def test_resume_delay(self):
  self.s.auto_sources_next=0;self.s.set_auto_collection(True)
  self.s.demo=False;self.assertFalse(self.s.auto_sources_due())

