import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_analysis_followup import DesktopService, FOLLOWUP


class AnalysisFollowupTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.s = DesktopService(Path(tmp.name), demo=True)
        self.addCleanup(self.s.close)
        self.s.demo = False
        self.s.model_names = ['test']

    def test_data_and_original_question_reach_provider(self):
        question = '工程を変更したら不良が減った。効果があったと断定できる？'
        reply = '前は100個中10個、後は40個中8個。期間はどちらも1週間。'
        with patch('tomeris_capabilities.core.generate_checked_response', return_value='母数を教えてください。') as gen:
            self.s.chat(question, 'test')
            self.s.chat(reply, 'test')
            provider = gen.call_args.args[0]
            self.assertIn(FOLLOWUP, provider.style)
            with patch.object(provider.base, 'generate', return_value='test') as model:
                provider.generate([{'role':'user','content':reply}])
            messages = model.call_args.args[0]
            self.assertIn({'role':'user','content':question}, messages)
            self.assertEqual(messages[-1]['content'], reply)
            self.assertNotIn(reply, provider.style)

    def test_no_context_no_followup(self):
        self.assertNotIn(FOLLOWUP, self.s.conversation_persona('100人です'))

    def test_topic_change_clears(self):
        self.s.track('原因は？', '人数は？')
        self.s.chat('別の話', 'test')
        self.assertNotIn(FOLLOWUP, self.s.conversation_persona('100人です'))

    def test_unrelated_numeric_question_excluded(self):
        self.s.track('原因は？', '人数は？')
        for text in ('明日の天気は？', '100年前の地震を調べて', 'こんにちは'):
            self.assertNotIn(FOLLOWUP, self.s.conversation_persona(text))

    def test_only_immediate_reply(self):
        self.s.track('原因は？', '人数は？')
        self.s.track('100人です', '未確認です')
        self.assertNotIn(FOLLOWUP, self.s.conversation_persona('期間は1週間です'))
