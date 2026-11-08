import unittest
from unittest.mock import patch
import tomeris_advice_v082 as quality
QUESTION='今日の作業に集中するための工夫を3つ挙げて'
GOOD='1. 机に今日終える作業を1つ書く。\n2. 通知を切り、短い時間だけ1つの作業を試す。\n3. スマホを手の届かない場所へ置く。'
class ConciseAdviceTests(unittest.TestCase):
    def test_new_unverified_label_flagged(self):
        bad=GOOD+'その時間は「フリーランド」と呼びます。'
        issues=quality.review_advice(QUESTION,bad)
        self.assertTrue(any('名称の根拠は未確認' in issue for issue in issues))
    def test_user_supplied_term_not_claimed_false(self):
        question='「ポモドーロ」という方法を使う工夫を3つ挙げて'
        answer=GOOD+'「ポモドーロ」と呼びます。'
        self.assertEqual(quality.review_advice(question,answer),[])
    def test_concise_advice_passes_verbose_retried(self):
        self.assertEqual(quality.review_advice(QUESTION,GOOD),[])
        self.assertTrue(quality.review_advice(QUESTION,GOOD+'説明。'*220))
        self.assertEqual(quality.review_advice(QUESTION+'。詳しく説明して',GOOD+'説明。'*220),[])
    def test_named_label_is_rewritten_once(self):
        with patch.object(quality.BaseProvider,'generate',side_effect=[GOOD+'「新しい方法」と呼びます。',GOOD]) as generate:
            answer=quality.AdviceProvider().generate([{'role':'user','content':QUESTION}])
        self.assertEqual(answer,GOOD)
        self.assertEqual(generate.call_count,2)
    def test_instruction_avoids_guarantees_and_requires_immediate_actions(self):
        self.assertIn('その場で着手できる行動',quality.DIRECT_RULES)
        self.assertIn('出典や研究結果を作らない',quality.DIRECT_RULES)
        self.assertNotIn('25分間',quality.DIRECT_RULES)
if __name__=='__main__':
    unittest.main()
