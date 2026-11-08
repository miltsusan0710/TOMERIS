import unittest
from unittest.mock import Mock, patch
from copy import deepcopy
import tomeris_advice_v083 as quality
import tomeris_v083 as app
from tomeris_provider import ProviderError

QUESTION='今日の作業に集中するための工夫を3つ挙げて'
GOOD='1. 通知を切り、25分間は1つの作業に取り組む。\n2. 紙に今日終える作業を1つ書く。\n3. 机からスマホを離し、5分休憩する。'
BAD='アドバイスやサポートを提供できます：\n1. 時間管理の支援\n2. 情報のフィルタリングを行いストレス軽減\n3. ユーザーと直接的なコミュニケーション'

class AdviceTests(unittest.TestCase):
    def test_pasted_bad_answer_detected_good_accepted(self):
        self.assertTrue(quality.review_advice(QUESTION,BAD))
        self.assertEqual(quality.review_advice(QUESTION,GOOD),[])

    def test_wrong_count_and_fullwidth_request(self):
        self.assertTrue(quality.review_advice(QUESTION,'1. 通知を切る'))
        self.assertEqual(quality.review_advice(QUESTION.replace('3','３'),GOOD),[])

    def test_capability_questions_and_pc_risk_not_misclassified(self):
        for question in ['AIが集中を支援する方法を教えて','PC操作のリスクへの具体策を3つ挙げて','トメリスのできることを教えて']:
            self.assertEqual(quality.review_advice(question,BAD),[])

    def test_retry_once_and_context_unchanged(self):
        messages=[{'role':'user','content':QUESTION}]
        before=deepcopy(messages)
        provider=quality.AdviceProvider()
        with patch.object(quality.BaseProvider,'generate',side_effect=[BAD,GOOD]) as generate:
            self.assertEqual(provider.generate(messages),GOOD)
            self.assertEqual(generate.call_count,2)
            self.assertIn('修正事項',generate.call_args.args[0][0]['content'])
        self.assertEqual(messages,before)

    def test_no_retry_on_good_answer(self):
        with patch.object(quality.BaseProvider,'generate',return_value=GOOD) as generate:
            self.assertEqual(quality.AdviceProvider().generate([{'role':'user','content':QUESTION}]),GOOD)
            self.assertEqual(generate.call_count,1)

    def test_warning_when_bad_twice_or_retry_failed(self):
        for replies in [[BAD,BAD],[BAD,ProviderError('offline')]]:
            with patch.object(quality.BaseProvider,'generate',side_effect=replies) as generate:
                result=quality.AdviceProvider().generate([{'role':'user','content':QUESTION}])
            self.assertIn('回答品質の注意',result)
            self.assertEqual(generate.call_count,2)

    def test_new_instructions_without_blanket_operation_footer(self):
        store=Mock()
        store.build_context.return_value='参考データ'
        store.recent_conversations.return_value=[]
        with patch.object(app,'read_core',return_value='基本人格'):
            messages=app.build_messages(store,QUESTION)
        self.assertIn('ユーザー自身が実行できる',messages[0]['content'])
        self.assertNotIn('未実行であることを明示してください',messages[0]['content'])
        self.assertEqual(messages[-1],{'role':'user','content':QUESTION})

if __name__=='__main__':
    unittest.main()
