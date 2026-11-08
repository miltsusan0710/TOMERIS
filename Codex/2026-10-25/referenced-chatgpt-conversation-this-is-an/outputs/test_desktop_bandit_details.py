import copy,json,unittest
from pathlib import Path
from tomeris_bandit_lab import experiment,evaluation_details
from tomeris_experiment_view import summary

class BanditDetailsTests(unittest.TestCase):
 def setUp(self):self.rows=json.loads(Path(__file__).with_name('bandit_synthetic_examples.json').read_text(encoding='utf-8'))
 def test_test_rewards_do_not_change_learned_policy_or_log(self):
  before=experiment(self.rows);changed=copy.deepcopy(self.rows)
  for row in changed:
   if row['split']=='test':row['rewards']={a:-r for a,r in row['rewards'].items()}
  after=experiment(changed)
  for key in ('policy','training_log','action_values','train_counts'):self.assertEqual(before[key],after[key])
  self.assertNotEqual(before['test_reward'],after['test_reward'])
  self.assertTrue(after['evaluation']['lower']>0)
 def test_cases_are_exactly_evaluation_rows(self):
  result=experiment(self.rows);detail=result['evaluation']
  expected={r['id'] for r in self.rows if r['split']=='test'}
  self.assertEqual({r['id'] for r in detail['cases']},expected)
  self.assertFalse(expected & {r['id'] for r in result['training_log']})
  self.assertEqual(detail['count'],detail['higher']+detail['equal']+detail['lower'])
  self.assertAlmostEqual(detail['mean_delta'],result['delta'])
 def test_topic_weighting_reveals_unequal_question_counts(self):
  rows=[dict(id=str(i),topic_id='many' if i<3 else 'one',context='overview',rewards={'search_order':0,'exact_title_first':1 if i<3 else -1}) for i in range(4)]
  detail=evaluation_details(rows,{'overview':'exact_title_first'})
  self.assertEqual(detail['mean_delta'],.5);self.assertEqual(detail['topic_mean_delta'],0)
  self.assertEqual(detail['lower'],1)
 def test_display_includes_regression_and_limits(self):
  result=experiment(self.rows);result['dataset_sha256']='test'
  text=summary(result)
  for value in ('低い','等しく重み付け','正誤の判定ではありません','統計的有意差'):self.assertIn(value,text)
