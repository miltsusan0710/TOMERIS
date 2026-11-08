import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v050 import DesktopService
class EditableCollectionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.s=DesktopService(Path(self.tmp.name)/'data',demo=True);self.addCleanup(self.s.close)
 def test_save_stops_without_budget_reset(self):
  self.s.auto_sources_index=2;self.s.save_collection_topics(['情報検索']);self.assertFalse(self.s.auto_sources_enabled);self.assertEqual(self.s.auto_sources_index,2)
  self.assertEqual(self.s.topic_store.load(),['情報検索'])
 def test_collect_uses_only_saved_topic(self):
  self.s.save_collection_topics(['情報検索']);self.s.set_auto_collection(True);self.s.auto_sources_next=0;self.s.demo=False
  page=dict(title='情報検索',url='https://ja.wikipedia.org/wiki/test',text='情報検索は必要な情報を探して取得するための手続きとして説明されています。')
  with patch('tomeris_editable_collection.wikipedia_search',return_value=[dict(title='情報検索')]) as search,patch('tomeris_editable_collection.wikipedia_page',return_value=page):
   self.s.collect_public_topic();search.assert_called_once_with('情報検索')
  self.assertEqual(len(self.s.collection_state()['results']),1)
 def test_corrupt_topics_stop(self):
  self.s.topic_store.path.write_bytes(b'{broken');path=self.s.data_dir;self.s.close();s=DesktopService(path,demo=True);self.addCleanup(s.close)
  self.assertFalse(s.auto_sources_enabled)
  with self.assertRaises(ValueError):s.set_auto_collection(True)
 def test_backup_restore_topics(self):
  self.s.save_collection_topics(['情報検索']);dest=Path(self.tmp.name)/'backup.zip';self.s.export_backup(dest);checked=self.s.inspect_backup(dest)
  self.assertEqual(checked['counts']['auto_topics'],1)
  folder=Path(self.s.restore_backup(dest,Path(self.tmp.name),checked['digest']));s=DesktopService(folder,demo=True);self.addCleanup(s.close)
  self.assertEqual(s.collection_topics,['情報検索']);self.assertFalse(s.auto_sources_enabled)
 def test_failed_topic_save_keeps_stopped(self):
  with patch.object(self.s.topic_store,'save',side_effect=OSError('test')):
   with self.assertRaises(OSError):self.s.save_collection_topics(['情報検索'])
  self.assertFalse(self.s.auto_sources_enabled)
