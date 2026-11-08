import unittest
from tomeris_evaluate_adaptation import evaluate

class AdaptationEvaluationTests(unittest.TestCase):
 def cases(self):return [dict(topic=t,group=t,split=s) for t,s in [('アルファベータ','train'),('論理学','train'),('ガンマデルタ','test'),('統計学','test')]]
 def search(self,topic):
  title={'アルファベータ':'アルファ・ベータ','ガンマデルタ':'ガンマ・デルタ'}.get(topic,topic)
  return [dict(title=title,url='https://example.org/'+title)]
 def page(self,row):return dict(**row,text=row['title']+'は試験のために用意した架空の説明文章であり、実際の事実を評価したものではありません。')
 def test_frozen_policy_and_shared_fetch(self):
  calls=[]
  def reader(row):calls.append(row['url']);return self.page(row)
  result=evaluate(self.cases(),self.search,reader)
  self.assertEqual(len(calls),4);self.assertFalse(result['overlap_detected'])
  self.assertEqual(result['comparison']['evidence'],2)
  self.assertEqual(result['comparison']['baseline_evidence'],2)
  self.assertEqual(result['policy'][0],'normalized')
  self.assertEqual(len(result['training_attempts']),3)
  self.assertFalse(result['production_enabled'])
 def test_overlap_suppresses_comparison(self):
  def search(topic):return [dict(title=topic,url='https://example.org/shared')]
  result=evaluate(self.cases(),search,self.page)
  self.assertTrue(result['overlap_detected']);self.assertIsNone(result['comparison'])
 def test_failures_remain_in_denominator(self):
  def search(topic):
   if topic=='統計学':raise OSError('offline')
   return self.search(topic)
  result=evaluate(self.cases(),search,self.page)
  self.assertEqual(result['comparison']['count'],2);self.assertEqual(result['comparison']['evidence'],1)
  self.assertEqual(result['records'][-1]['search_error'],'offline')
 def test_split_rejection_before_network(self):
  cases=self.cases();cases[-1]['group']=cases[0]['group']
  with self.assertRaises(ValueError):evaluate(cases,lambda _:self.fail('network'),self.page)
