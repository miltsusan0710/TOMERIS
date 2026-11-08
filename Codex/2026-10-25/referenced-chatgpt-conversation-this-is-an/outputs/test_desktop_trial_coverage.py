import unittest,json
import test_desktop_trial_export as fixtures
from tomeris_trial_coverage import summarize,classify
from tomeris_research_trials import digest

class CoverageTests(unittest.TestCase):
 def setUp(self):
  self.fixture=fixtures.ExportTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups);self.root=self.fixture.root
 def test_all_records_included_without_review_duplicates(self):
  before={p.name:p.read_bytes() for p in self.root.iterdir()}
  result=summarize(self.root)
  self.assertEqual(result['total'],4);self.assertEqual(result['counts']['both_have_evidence'],4)
  self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.iterdir()})
 def test_failure_and_missing_evidence(self):
  for i,status in enumerate(['failed','retrieved']):
   path=self.root/self.fixture.manifest[i]['record'];env=json.loads(path.read_text(encoding='utf-8'))
   env['record']['pages'][0].update(status=status,excerpts=[])
   env['sha256']=digest(env['record']);path.write_text(json.dumps(env),encoding='utf-8')
  result=summarize(self.root)
  self.assertEqual(result['counts']['retrieval_failed'],1);self.assertEqual(result['counts']['no_matching_evidence'],1)
  self.assertEqual(sum(result['counts'].values()),4)
 def test_search_failure_and_empty_results_distinct(self):
  record=dict(candidates=[],pages=[],rankings={},error='timeout')
  self.assertEqual(classify(record),'search_error');record['error']=''
  self.assertEqual(classify(record),'no_candidates')
 def test_invalid_not_silently_dropped_and_missing_directory_not_created(self):
  path=self.root/self.fixture.manifest[0]['record'];path.write_text('{}',encoding='utf-8')
  result=summarize(self.root);self.assertEqual(result['total'],4);self.assertEqual(result['counts']['invalid'],1)
  absent=self.root/'absent';self.assertEqual(summarize(absent)['total'],0);self.assertFalse(absent.exists())
