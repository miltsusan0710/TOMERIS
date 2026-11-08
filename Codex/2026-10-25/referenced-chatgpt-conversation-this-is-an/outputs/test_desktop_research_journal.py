import unittest,json
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from tomeris_research_journal import ResearchJournal,validate,MAX_BYTES
class ResearchJournalTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.j=ResearchJournal(self.tmp.name)
 def add(self,q='質問'):
  return self.j.append(q,'Wikipedia',[dict(title='資料',url='https://example.com/article')])
 def test_roundtrip_reopen_metadata_only(self):
  r=self.add();self.assertEqual(ResearchJournal(self.tmp.name).get(r['id']),r)
  self.assertEqual(set(r),{'id','question','method','sources','retrieved_at'})
 def test_invalid_existing_preserved(self):
  self.j.path.write_bytes(b'{invalid');before=self.j.path.read_bytes()
  with self.assertRaises(ValueError):self.add()
  self.assertEqual(self.j.path.read_bytes(),before)
 def test_bounded_retention(self):
  for i in range(102):self.add(str(i))
  rows=self.j.read();self.assertEqual(len(rows),100);self.assertEqual(rows[0]['question'],'2')
 def test_individual_delete(self):
  a=self.add('a');b=self.add('b');self.j.delete(a['id']);self.assertEqual(self.j.read(),[b])
  with self.assertRaises(ValueError):self.j.delete(a['id'])
 def test_bad_sources_dates_and_duplicates(self):
  r=self.add()
  for url in ('http://127.0.0.1/test','https://user:pass@example.com/','https://example.com/a b'):
   invalid=dict(r,sources=[dict(title='資料',url=url)])
   with self.assertRaises(ValueError):validate(dict(version=1,records=[invalid]))
  with self.assertRaises(ValueError):validate(dict(version=1,records=[dict(r,retrieved_at='2026-10-29')]))
  with self.assertRaises(ValueError):validate(dict(version=1,records=[r,r]))
 def test_failed_replace_preserves_data_and_cleans_temp(self):
  self.add();before=self.j.path.read_bytes()
  with patch('tomeris_research_journal.os.replace',side_effect=OSError('test')):
   with self.assertRaises(OSError):self.add('new')
  self.assertEqual(self.j.path.read_bytes(),before);self.assertEqual(list(Path(self.tmp.name).glob('*.tmp')),[])
 def test_size_limit_read(self):
  self.j.path.write_bytes(b' '*(MAX_BYTES+1))
  with self.assertRaises(ValueError):self.j.read()
 def test_input_detached_and_empty_source_rejected(self):
  r=self.add();r['sources'].clear();self.assertEqual(len(self.j.read()[0]['sources']),1)
  with self.assertRaises(ValueError):self.j.append('q','method',[])
