import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v043 import DesktopService
from tomeris_backup_v034 import DesktopService as OldBackup

GOOD='Ollamaはローカル環境でモデルを実行するためのツールとして説明されています。'
class ResearchHistoryServiceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.s=DesktopService(Path(self.tmp.name)/'data',demo=True);self.addCleanup(self.s.close)
 def ask(self,q):return self.s.web_chat(q,'unused',automatic=True)
 def research(self,success=True):
  self.s.demo=False;row=dict(title='Ollamaの説明',url='https://example.com/ollama',snippet=GOOD)
  with patch.object(self.s.methods,'candidates',return_value=([row],[])),patch('tomeris_evidence_v029.fetch_page',return_value=dict(row,text=GOOD if success else '無関係',published='')):
   return self.ask('Ollamaについて調べて')
 def test_report_persist_and_past_display_without_search(self):
  self.research();rows=self.s.research_journal.read();self.assertEqual(len(rows),1)
  with patch.object(self.s.methods,'candidates',side_effect=AssertionError('no search')):
   self.assertIn(rows[0]['id'],self.ask('調査履歴を見せて'))
   answer=self.ask('/research-show '+rows[0]['id']);self.assertIn('再取得していません',answer);self.assertIn('https://example.com/ollama',answer)
  self.assertEqual(len(self.s.research_journal.read()),1)
 def test_no_sources_no_history(self):
  self.research(False);self.assertEqual(self.s.research_journal.read(),[])
 def test_corrupt_history_does_not_hide_answer(self):
  p=self.s.research_journal.path;p.write_bytes(b'{broken')
  answer=self.research();self.assertIn(GOOD,answer);self.assertIn('保存できません',answer);self.assertEqual(p.read_bytes(),b'{broken')
 def test_delete_does_not_touch_catalogue(self):
  self.research();before=(self.s.data_dir/'research_sources.json').read_bytes();r=self.s.research_journal.read()[0]
  self.ask('/research-delete '+r['id']);self.assertEqual(self.s.research_journal.read(),[])
  self.assertEqual(before,(self.s.data_dir/'research_sources.json').read_bytes())
 def test_backup_restore_new_and_old(self):
  self.research();dest=Path(self.tmp.name)/'new.zip';self.s.export_backup(dest)
  checked=self.s.inspect_backup(dest);self.assertEqual(checked['counts']['research_history'],1)
  restored=Path(self.s.restore_backup(dest,Path(self.tmp.name),checked['digest']))
  self.assertEqual((restored/'research_history.json').read_bytes(),self.s.research_journal.path.read_bytes())
  old=Path(self.tmp.name)/'old.zip';OldBackup.export_backup(self.s,old)
  self.assertNotIn('research_history.json',self.s.inspect_backup(old)['files'])
 def test_invalid_history_backup_refused(self):
  self.s.research_journal.path.write_bytes(b'{"version":1,"records":[{}]}')
  dest=Path(self.tmp.name)/'bad.zip'
  with self.assertRaises(ValueError):self.s.export_backup(dest)
  self.assertFalse(dest.exists())
