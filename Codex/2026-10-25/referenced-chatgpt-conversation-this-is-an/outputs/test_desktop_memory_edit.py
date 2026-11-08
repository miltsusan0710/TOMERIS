import unittest
from tempfile import TemporaryDirectory
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from tomeris_memory_edit import DesktopService

class MemoryEditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.s=DesktopService(self.tmp.name,demo=True)
        self.s.remember('Ｐｙｔｈｏｎを学ぶ','目標'); self.s.remember('毎日散歩する','習慣')
    def tearDown(self): self.s.close(); self.tmp.cleanup()
    def row(self): return self.s.find_memories('python')['rows'][0]
    def test_search_readonly_detached(self):
        before=self.s.memory_path.read_bytes(); row=self.row(); row['text']='changed'
        self.assertEqual(self.s.memory_path.read_bytes(),before)
        self.assertEqual(self.row()['text'],'Ｐｙｔｈｏｎを学ぶ')
        self.assertEqual(self.s.find_memories('python 目標')['total'],1)
        self.assertEqual(self.s.find_memories('missing')['total'],0)
    def test_save_history_restart_preserve_metadata(self):
        row=self.row(); original=deepcopy(self.s.store.data['memories'][0])
        self.s.edit_memory(row['id'],row['_revision'],'Pythonを毎日学ぶ')
        self.s.close(); self.s=DesktopService(self.tmp.name,demo=True)
        updated=self.row()
        self.assertEqual(updated['edit_history'][0]['text'],original['text'])
        for key in original:
            if key!='text': self.assertEqual(updated[key],original[key])
        context=self.s.store.build_context('Python')
        self.assertNotIn(original['text'],context); self.assertIn(updated['text'],context)
    def test_stale_edit_rejected(self):
        row=self.row(); self.s.edit_memory(row['id'],row['_revision'],'Python練習')
        with self.assertRaises(ValueError): self.s.edit_memory(row['id'],row['_revision'],'古い編集')
        self.assertEqual(self.row()['text'],'Python練習')
    def test_failed_replace_rolls_back(self):
        row=self.row(); before=self.s.memory_path.read_bytes(); data=deepcopy(self.s.store.data)
        with patch.object(Path,'replace',side_effect=OSError('test failure')), self.assertRaises(OSError):
            self.s.edit_memory(row['id'],row['_revision'],'Python練習')
        self.assertEqual(self.s.memory_path.read_bytes(),before); self.assertEqual(self.s.store.data,data)
        self.s.edit_memory(row['id'],row['_revision'],'Python練習')
        self.assertEqual(len(self.row()['edit_history']),1)
    def test_invalid_duplicate_noop(self):
        row=self.row(); before=self.s.memory_path.read_bytes()
        for text in ['', ' '*3,'x'*10001,'毎日散歩する']:
            with self.assertRaises(ValueError): self.s.edit_memory(row['id'],row['_revision'],text)
        self.s.edit_memory(row['id'],row['_revision'],row['text'])
        self.assertEqual(self.s.memory_path.read_bytes(),before)
    def test_paging(self):
        self.s.store.data['memories'] += [dict(id=f'T{i}',text=f'match {i}') for i in range(55)]
        first=self.s.find_memories('match'); second=self.s.find_memories('match',50)
        self.assertEqual(len(first['rows']),50); self.assertEqual(len(second['rows']),5)
        self.assertEqual(self.s.find_memories('match',999)['offset'],50)
    def test_multiple_edits_keep_all_versions(self):
        row=self.row(); self.s.edit_memory(row['id'],row['_revision'],'Python第一版')
        row=self.row(); self.s.edit_memory(row['id'],row['_revision'],'Python第二版')
        self.assertEqual([x['text'] for x in self.row()['edit_history']],['Ｐｙｔｈｏｎを学ぶ','Python第一版'])

if __name__=='__main__': unittest.main()
