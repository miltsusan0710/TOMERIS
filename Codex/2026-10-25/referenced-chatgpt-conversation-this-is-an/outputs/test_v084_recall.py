from copy import deepcopy
import unittest
from unittest.mock import Mock
import tomeris_recall_v084 as recall
import tomeris_v084 as app

class RecallTests(unittest.TestCase):
    def store(self,records):
        store=Mock()
        store.data={'memories':records}
        return store
    def test_development_goal_not_rewritten_or_sent_to_model(self):
        text='トメリスの最重要目標は、ユーザーの思考力・判断力・行動力・精神的な回復力を高める専属AIパートナーになること。中心原則は長期的な勝利。'
        store=self.store([{'id':'M0001','category':'目標','text':text}])
        before=deepcopy(store.data)
        provider=Mock(cloud=False)
        answer=app.generate_checked_response(provider,store,'記憶を参照して：私の目標を教えて')
        self.assertIn('「'+text+'」',answer)
        self.assertIn('トメリスの役割・開発目標',answer)
        self.assertIn('保証を意味しません',answer)
        self.assertNotIn('勝利を保証します',answer)
        provider.generate.assert_not_called()
        store.save.assert_not_called()
        self.assertEqual(store.data,before)
    def test_personal_goal_preserves_owner(self):
        original='私の目標は毎週1冊本を読むこと。'
        result=recall.goal_recall(self.store([{'id':'M0002','category':'目標','text':original}]),'私の目標を教えて')
        self.assertIn(original,result)
        self.assertNotIn('この記録はトメリスの役割',result)
    def test_unknown_goal_not_invented(self):
        result=recall.goal_recall(self.store([]),'私の目標を教えて')
        self.assertIn('見つかりません',result)
    def test_general_advice_still_uses_model(self):
        self.assertIsNone(recall.goal_recall(self.store([]),'目標を達成する工夫を3つ挙げて'))
        self.assertIsNone(recall.goal_recall(self.store([]),'私の目標を変更して'))
    def test_multiple_owners_are_quoted_separately(self):
        records=[{'id':'M1','category':'目標','text':'トメリスの目標は支援すること'}, {'id':'M2','category':'目標','text':'私の目標は読書'}]
        answer=recall.goal_recall(self.store(records),'私の目標を教えて')
        self.assertIn('[M1]',answer)
        self.assertIn('[M2]',answer)
        self.assertIn('主体は原文で確認',answer)
if __name__=='__main__':
    unittest.main()
