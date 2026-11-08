import unittest,tempfile,json
from pathlib import Path
from tomeris_adaptive_collection import fetch,order,DesktopService

class OutcomeTests(unittest.TestCase):
 def test_transport_error_is_recorded_but_not_a_strategy_penalty(self):
  def fail(row):raise OSError('offline')
  item,attempts=fetch('統計学',['exact','normalized'],search=lambda _: [dict(title='統計学',url='https://example.org/a')],page_reader=fail)
  self.assertIsNone(item);self.assertTrue(all(r['outcome']=='retrieval_error' for r in attempts))
  history=[dict(action='exact',success=True),dict(action='normalized',success=False)]
  self.assertEqual(order(history+attempts*50),order(history))
 def test_no_candidate_and_no_evidence_are_separate(self):
  _,missing=fetch('統計学',['exact'],search=lambda _:[])
  _,empty=fetch('統計学',['exact'],search=lambda _: [dict(title='統計学',url='https://example.org/a')],page_reader=lambda _:dict(text='広告'))
  self.assertEqual(missing[0]['outcome'],'no_candidate');self.assertEqual(empty[0]['outcome'],'no_evidence')
 def test_inconsistent_persisted_result_is_preserved_and_disabled(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'retrieval_experience.json';data=json.dumps(dict(version=1,attempts=[dict(action='exact',success=True,outcome='retrieval_error')]))
   path.write_text(data);s=DesktopService(Path(folder),demo=True)
   try:self.assertTrue(s.adaptive_error);self.assertEqual(path.read_text(),data)
   finally:s.close()
 def test_outcomes_survive_restart(self):
  with tempfile.TemporaryDirectory() as folder:
   s=DesktopService(Path(folder),demo=True)
   s.remember_attempts([dict(action='exact',success=False,outcome='retrieval_error')]);s.close()
   s=DesktopService(Path(folder),demo=True)
   try:self.assertEqual(s.adaptive_history[0]['outcome'],'retrieval_error')
   finally:s.close()
