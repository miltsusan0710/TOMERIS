import unittest,json
import test_desktop_trial_export as fixtures
from tomeris_trial_times import validate_times
from tomeris_trial_export import export
from tomeris_research_trials import digest

class TrialTimeTests(unittest.TestCase):
 def record(self):
  return dict(started_at='2026-11-05T00:00:00Z',finished_at='2026-11-05T00:01:00Z',pages=[dict(checked_at='2026-11-05T00:00:30Z')])
 def test_timezone_offsets_compare_as_instants(self):
  validate_times(self.record(),dict(reviewed_at='2026-11-05T09:01:00+09:00'))
  with self.assertRaises(ValueError):validate_times(self.record(),dict(reviewed_at='2026-11-05T09:00:59+09:00'))
 def test_missing_invalid_and_naive_timestamps(self):
  for value in (None,'yesterday','2026-11-05T00:01:00',42):
   with self.subTest(value=value):
    with self.assertRaises(ValueError):validate_times(dict(self.record(),finished_at=value),dict(reviewed_at='2026-11-05T00:02:00Z'))
 def test_request_outside_period_and_reversed_period(self):
  for field,value in [('started_at','2026-11-05T00:02:00Z'),('checked_at','2026-11-04T23:59:59Z'),('checked_at','2026-11-05T00:02:00Z')]:
   record=self.record()
   if field=='checked_at':record['pages'][0][field]=value
   else:record[field]=value
   with self.assertRaises(ValueError):validate_times(record,dict(reviewed_at='2026-11-05T00:03:00Z'))
 def test_legacy_optional_request_times_not_fabricated(self):
  record=dict(finished_at='2026-11-05T00:01:00Z',pages=[{}]);before=json.dumps(record)
  validate_times(record,dict(reviewed_at='2026-11-05T00:02:00Z'));self.assertEqual(json.dumps(record),before)
 def test_export_missing_time_refuses_before_writing(self):
  fixture=fixtures.ExportTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
  entry=fixture.manifest[0];path=fixture.root/entry['record'];env=json.loads(path.read_text(encoding='utf-8'))
  del env['record']['finished_at'];env['sha256']=digest(env['record']);path.write_text(json.dumps(env),encoding='utf-8')
  path=fixture.root/entry['review'];review=json.loads(path.read_text(encoding='utf-8'));review['record_sha256']=env['sha256'];path.write_text(json.dumps(review),encoding='utf-8')
  out=fixture.root/'dataset.json'
  with self.assertRaises(ValueError):export(fixture.root,fixture.manifest,out)
  self.assertFalse(out.exists())
