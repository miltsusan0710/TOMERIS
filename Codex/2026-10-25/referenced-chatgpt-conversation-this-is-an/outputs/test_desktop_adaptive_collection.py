import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
from tomeris_adaptive_collection import DesktopService,order,fetch

class AdaptiveCollectionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def service(self):
  s=DesktopService(self.root,demo=True);self.addCleanup(s.close);return s
 def test_observed_success_changes_order_and_survives_restart(self):
  s=self.service();s.remember_attempts([dict(action='exact',success=False),dict(action='normalized',success=True)])
  self.assertEqual(order(s.adaptive_history)[0],'normalized')
  s.close()
  other=self.service();self.assertEqual(other.adaptive_history,s.adaptive_history)
 def test_punctuation_fallback_and_verbatim_evidence(self):
  page=dict(title='トニー・スターク',url='https://example.org/a',text='トニー・スタークは架空の登場人物であり、これは取得処理だけを調べるための人工文章です。')
  with patch('tomeris_adaptive_collection.wikipedia_search',return_value=[dict(title=page['title'],url=page['url'])]),patch('tomeris_adaptive_collection.wikipedia_page',return_value=page) as get:
   item,attempts=fetch('トニースターク',['exact','normalized'])
  self.assertEqual([r['success'] for r in attempts],[False,True]);self.assertEqual(get.call_count,1)
  self.assertTrue(all(q in page['text'] for q in item['excerpts']))
 def test_unrelated_text_never_gets_success_reward(self):
  with patch('tomeris_adaptive_collection.wikipedia_search',return_value=[dict(title='論理学',url='https://example.org/a')]),patch('tomeris_adaptive_collection.wikipedia_page',return_value=dict(text='広告です。')) as get:
   item,attempts=fetch('論理学',['exact','normalized'])
  self.assertIsNone(item);self.assertFalse(any(r['success'] for r in attempts));self.assertEqual(get.call_count,1)
 def test_corrupt_experience_preserved(self):
  path=self.root/'retrieval_experience.json';path.write_text('broken')
  s=self.service();self.assertTrue(s.adaptive_error);s.remember_attempts([dict(action='exact',success=True)])
  self.assertEqual(path.read_text(),'broken')
 def test_stopped_and_demo_never_fetch(self):
  s=self.service();s.auto_sources_next=0
  with patch('tomeris_adaptive_collection.fetch',side_effect=AssertionError('network')):
   self.assertIsNone(s.collect_public_topic());s.demo=False;s.set_auto_collection(False);self.assertIsNone(s.collect_public_topic())
 def test_collection_updates_on_worker_and_preserves_budget(self):
  s=self.service();s.demo=False;s.auto_sources_next=0
  with patch('tomeris_adaptive_collection.fetch',return_value=(None,[dict(action='exact',success=False),dict(action='normalized',success=False)])) as get:
   s.collect_public_topic();self.assertEqual(get.call_count,2)
   self.assertIsNone(s.collect_public_topic());self.assertEqual(get.call_count,2)
  self.assertEqual(s.auto_sources_index,2);self.assertEqual(len(s.adaptive_history),4)
  self.assertEqual(len(s.topic_results),2)
 def test_history_bounded(self):
  s=self.service();s.remember_attempts([dict(action='exact',success=True)]*501)
  self.assertEqual(len(s.adaptive_history),500)
