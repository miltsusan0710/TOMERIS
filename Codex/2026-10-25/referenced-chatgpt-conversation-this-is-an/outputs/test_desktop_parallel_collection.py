import unittest,threading
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v051 import DesktopService

def item(topic):return dict(page=dict(title=topic,url='https://ja.wikipedia.org/wiki/'+str(len(topic)),text='unused'),excerpts=[topic+'は考え方を整理するための概念として説明されています。'])
class ParallelCollectionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.s=DesktopService(Path(self.tmp.name),demo=True);self.addCleanup(self.s.close);self.s.demo=False;self.s.auto_sources_next=0
 def test_two_reads_overlap_writes_serialized(self):
  barrier=threading.Barrier(2);threads=[];owner=threading.get_ident();writes=[]
  def fetch(topic):threads.append(threading.get_ident());barrier.wait(timeout=3);return item(topic)
  original=self.s.catalogue.learn
  def learn(items):writes.append(threading.get_ident());return original(items)
  with patch('tomeris_parallel_collection.fetch_topic',side_effect=fetch),patch.object(self.s.catalogue,'learn',side_effect=learn):self.s.collect_public_topic()
  self.assertEqual(len(set(threads)),2);self.assertEqual(writes,[owner,owner]);self.assertEqual(self.s.auto_sources_index,2);self.assertEqual(len(self.s.topic_results),2)
 def test_third_then_limit(self):
  with patch('tomeris_parallel_collection.fetch_topic',side_effect=item) as fetch:
   self.s.collect_public_topic();self.assertEqual(fetch.call_count,2)
   self.assertIsNone(self.s.collect_public_topic());self.s.auto_sources_next=0;self.s.collect_public_topic();self.assertEqual(fetch.call_count,3)
   self.s.auto_sources_next=0;self.assertIsNone(self.s.collect_public_topic())
 def test_one_failure_does_not_discard_other(self):
  def fetch(topic):
   if topic==self.s.collection_topics[0]:raise OSError('offline')
   return item(topic)
  with patch('tomeris_parallel_collection.fetch_topic',side_effect=fetch):self.s.collect_public_topic()
  self.assertIn('失敗',self.s.topic_results[0]['status']);self.assertIn('1件保存',self.s.topic_results[1]['status'])
 def test_stopped_no_requests(self):
  self.s.set_auto_collection(False)
  with patch('tomeris_parallel_collection.fetch_topic',side_effect=AssertionError('stopped')):self.assertIsNone(self.s.collect_public_topic())
 def test_one_remaining_topic_only(self):
  self.s.collection_topics=['論理学']
  with patch('tomeris_parallel_collection.fetch_topic',side_effect=item) as fetch:self.s.collect_public_topic();self.assertEqual(fetch.call_count,1)
