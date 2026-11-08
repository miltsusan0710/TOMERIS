import copy,json,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v072 import DesktopService
from tomeris_bandit_lab import experiment,validate

class DistinctTests(unittest.TestCase):
 def setUp(self):
  tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);self.s=DesktopService(Path(tmp.name),demo=True);self.addCleanup(self.s.close);self.s.demo=False
 def test_mirrors_not_counted_or_saved_twice(self):
  text='トニー・スタークは、物語の主人公として登場する人物と説明されています。'
  rows=[dict(title='紹介',url='https://'+host+'/article',snippet=text) for host in ('example.org','example.com')]
  def page(url):return dict(title='紹介',url=url,text=text,published='',provider='公開ページ')
  with patch('tomeris_research_learning.BaseMethods.candidates',return_value=(rows,[])),patch('tomeris_evidence_v029.fetch_page',side_effect=page):
   answer=self.s.report('トニースターク')
   self.assertEqual(len(self.s.last_evidence_items),1);self.assertEqual(len(self.s.catalogue.rows),1);self.assertIn('重複した原文',answer)
   answer2=self.s.report('トニースターク');self.assertEqual(len(self.s.last_evidence_items),1)
 def test_new_excerpt_retained_and_original_preserved(self):
  self.s._seen_excerpts=set();self.s._duplicate_count=0
  quote='情報検索は、必要な情報を資料から探し出すための方法として説明されています。'
  other='情報検索は、対象となる資料や検索語を選んで進める作業として説明されています。'
  with patch('tomeris_detail_followup.DesktopService.extract_passages',side_effect=[[quote],[quote,other]]):
   self.assertEqual(self.s.extract_passages({},''),[quote]);self.assertEqual(self.s.extract_passages({},''),[other])

class BanditTests(unittest.TestCase):
 def setUp(self):self.rows=json.loads(Path(__file__).with_name('bandit_synthetic_examples.json').read_text(encoding='utf-8'))
 def test_simulated_feedback_changes_policy(self):
  result=experiment(self.rows)
  self.assertEqual(result['policy'],{'overview':'exact_title_first','specific':'search_order'})
  self.assertGreater(result['delta'],0);self.assertTrue(result['synthetic']);self.assertFalse(result['production_enabled'])
 def test_test_rewards_never_train_policy(self):
  a=experiment(self.rows)
  for row in self.rows:
   if row['split']=='test':row['rewards']={k:-v for k,v in row['rewards'].items()}
  b=experiment(self.rows)
  self.assertEqual(a['policy'],b['policy']);self.assertEqual(a['action_values'],b['action_values']);self.assertNotEqual(a['test_reward'],b['test_reward'])
 def test_invalid_feedback_rejected(self):
  for mutate in [lambda r:r[-1].update(topic_id=r[0]['topic_id']),lambda r:r[0]['rewards'].pop('search_order'),lambda r:r[0]['rewards'].update(search_order=float('nan')),lambda r:r[0].update(reason=''),lambda r:r[0].update(origin='ai_guess')]:
   rows=copy.deepcopy(self.rows);mutate(rows)
   with self.assertRaises(ValueError):validate(rows)
 def test_only_training_selected_actions_update(self):
  result=experiment(self.rows);training={r['id']:r for r in self.rows if r['split']=='train'}
  self.assertEqual(len(result['training_log']),len(training)*20)
  for step in result['training_log']:self.assertEqual(step['reward'],training[step['id']]['rewards'][step['action']])
