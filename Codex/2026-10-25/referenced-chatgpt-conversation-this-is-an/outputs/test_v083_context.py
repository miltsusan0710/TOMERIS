import unittest
from unittest.mock import Mock, patch
import tomeris_context_v083 as context
import tomeris_advice_v083 as quality
import tomeris_v083 as app

class ContextTests(unittest.TestCase):
    def store(self):
        store=Mock()
        store.search_memory.return_value=[{'text':'目標情報'*300}]
        store.search_growth.return_value=[]
        store.search_knowledge.return_value=[]
        store.recent_conversations.return_value=[{'user':'以前の質問','tomeris':'以前の回答'}]
        return store
    def test_plain_question_is_short_and_never_retrieves(self):
        store=self.store()
        core=Mock(side_effect=AssertionError)
        messages=context.build_short_messages(store,'集中する工夫を3つ挙げて',core_supplier=core)
        self.assertEqual(len(messages),2)
        self.assertLess(len(messages[0]['content']),350)
        store.search_memory.assert_not_called()
        store.recent_conversations.assert_not_called()
        core.assert_not_called()
    def test_memory_is_gated_and_bounded(self):
        store=self.store()
        messages=context.build_short_messages(store,'私の目標を記憶から教えて')
        store.search_memory.assert_called_once()
        store.recent_conversations.assert_not_called()
        self.assertLess(len(messages[1]['content']),1700)
        self.assertIn('目標情報',messages[1]['content'])
        store.save.assert_not_called()
    def test_followup_and_persona_are_explicit(self):
        store=self.store()
        messages=context.build_short_messages(store,'前回の続き。基本人格に沿って',core_supplier=lambda:'PERSONA')
        self.assertIn('以前の回答',str(messages))
        self.assertIn('PERSONA',str(messages))
    def test_no_second_long_system_prompt_from_provider(self):
        messages=[{'role':'system','content':'short'},{'role':'user','content':'hello'}]
        with patch.object(quality.BaseProvider,'generate',return_value='hello') as generate:
            quality.AdviceProvider().generate(messages)
        self.assertEqual(generate.call_args.args[0],messages)
    def test_risk_rules_only_for_risk_questions(self):
        plain=app.build_messages(self.store(),'集中する工夫は？')
        risk=app.build_messages(self.store(),'PC操作のリスクを3つ挙げて')
        self.assertNotIn('実行前の確認',plain[0]['content'])
        self.assertIn('実行前の確認',risk[0]['content'])

if __name__=='__main__':
    unittest.main()
