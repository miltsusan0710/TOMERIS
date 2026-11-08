import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v041 import DesktopService
from tomeris_plans import today
class TomorrowTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.tmp.cleanup);self.addCleanup(self.s.close)
  self.s.save_plan('確認',15,[dict(title='完了の作業',minutes=5),dict(title='残す作業',minutes=10)],today())
 def draft(self):return self.s.tomorrow_draft(self.s.today_plan()['id'])
 def test_exclude_done_and_preserve_original(self):
  original=self.s._plans()[0].copy();r=self.s.today_plan();self.s.set_completion(r['id'],0,True)
  d=self.draft();self.assertEqual([t['title'] for t in d['tasks']],['残す作業'])
  self.s.save_tomorrow_draft(d['token'],[0]);self.assertEqual(self.s._plans()[0],original)
  self.assertEqual(self.s._plans()[-1]['date'],d['date'])
  with self.assertRaises(ValueError):self.s.save_tomorrow_draft(d['token'],[0])
 def test_cancel_draft_does_not_write(self):
  p=self.s.data_dir/'daily_plans.json';before=p.read_bytes();self.draft();self.assertEqual(before,p.read_bytes())
 def test_stale_progress_blocks_save(self):
  d=self.draft();r=self.s.today_plan();self.s.set_completion(r['id'],0,True)
  with self.assertRaises(ValueError):self.s.save_tomorrow_draft(d['token'],[0])
 def test_midnight_blocks_save(self):
  d=self.draft()
  with patch('tomeris_tomorrow_plans.today',return_value=d['date']):
   with self.assertRaises(ValueError):self.s.save_tomorrow_draft(d['token'],[0])
 def test_identical_content_not_duplicated(self):
  d=self.draft();self.s.save_tomorrow_draft(d['token'],[0,1]);d=self.draft();self.assertTrue(d['existing'])
  with self.assertRaises(ValueError):self.s.save_tomorrow_draft(d['token'],[0,1])
  self.assertEqual(len(self.s._plans()),2)
 def test_selection_and_unknown_completion(self):
  d=self.draft();self.assertFalse(d['recorded'])
  for indices in ([],[0,0],[True],[99]):
   with self.assertRaises(ValueError):self.s.save_tomorrow_draft(d['token'],indices)
 def test_io_failure_preserves_file(self):
  d=self.draft();p=self.s.data_dir/'daily_plans.json';before=p.read_bytes()
  with patch('tomeris_tomorrow_plans.os.replace',side_effect=OSError('test')):
   with self.assertRaises(OSError):self.s.save_tomorrow_draft(d['token'],[0])
  self.assertEqual(before,p.read_bytes())
