import unittest,tempfile,json
from pathlib import Path
from tomeris_source_catalogue import Catalogue
from tomeris_learning_review import ReviewCatalogue,reasons
from unittest.mock import patch
from tomeris_learning_review import DesktopService

def item(text,title='資料'):
 return dict(page=dict(title=title,url='https://example.org/'+title,text=text),excerpts=[text])

class LearningReviewTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)
  self.base=Catalogue(self.path);self.gate=ReviewCatalogue(self.base,self.path/'review.json')
 def test_pending_is_not_learned_and_safe_item_continues(self):
  count=self.gate.learn([item('暴力を推奨するという記述。','保留資料'),item('科学的方法についての説明。','安全資料')])
  self.assertEqual(count,1);self.assertEqual([r['title'] for r in self.base.rows],['安全資料'])
  self.assertEqual(len(self.gate.review_rows),1)
 def test_approval_is_exact_revision_and_persists(self):
  first=item('暴力を推奨するという記述。');self.gate.learn([first]);ident=next(iter(self.gate.review_rows))
  self.gate.decide(ident,True);self.assertEqual(len(self.base.rows),1)
  again=ReviewCatalogue(self.base,self.path/'review.json');self.assertEqual(again.review_rows[ident]['status'],'approved')
  again.learn([item('暴力を推奨するという変更後の記述。')])
  self.assertEqual(sum(r['status']=='pending' for r in again.review_rows.values()),1)
 def test_rejected_is_not_requeued(self):
  data=item('テロを支持するという記述。');self.gate.learn([data]);ident=next(iter(self.gate.review_rows))
  self.gate.decide(ident,False);self.assertEqual(self.gate.learn([data]),0);self.assertEqual(len(self.gate.review_rows),1)
 def test_politics_or_religion_alone_not_flagged(self):
  self.assertEqual(reasons('政治制度、宗教の歴史と民主主義について学ぶ。'),[])
  self.assertTrue(reasons('特定の民族を排除すべきと主張している。'))
 def test_corrupt_queue_kept_and_fail_closed(self):
  path=self.path/'broken.json';path.write_text('{broken',encoding='utf-8')
  gate=ReviewCatalogue(self.base,path)
  self.assertTrue(gate.review_error);self.assertEqual(gate.learn([item('通常資料')]),0)
  self.assertEqual(path.read_text(),'{broken')
 def test_collector_continues_and_pending_topic_skipped(self):
  s=DesktopService(self.path/'app',demo=True)
  try:
   def fetch(topic,actions):
    text='暴力を推奨するという記述。' if topic=='論理的思考' else '情報を確認するための資料です。'
    return item(text,topic),[dict(action='exact',success=True,outcome='evidence')]
   with patch.object(s,'auto_sources_due',return_value=True),patch('tomeris_adaptive_collection.fetch',side_effect=fetch):
    result=s.collect_public_topic()
   self.assertIn('確認待ち',result)
   self.assertEqual(len(s.catalogue.rows),1)
   s.rotation_recent={}
   self.assertNotIn('論理的思考',s.eligible_topics())
   self.assertIn('統計学',s.eligible_topics())
  finally:s.close()
