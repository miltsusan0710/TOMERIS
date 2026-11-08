import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from tomeris_desktop_v060 import DesktopService


class PeopleTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.s = DesktopService(Path(tmp.name), demo=True)
        self.addCleanup(self.s.close)

    def test_user_kun_prompt_and_role_followup(self):
        self.s.demo = False
        with patch('tomeris_capabilities.core.generate_checked_response', side_effect=AssertionError('no unsupported refusal')):
            answer = self.s.web_chat('kunて誰？', 'unused', automatic=True)
            self.assertIn('どの分野', answer)
            self.assertNotIn('提供できません', answer)
            with patch.object(self.s, 'report', return_value='公開資料の報告') as report:
                self.assertEqual('公開資料の報告', self.s.web_chat('YouTuber', 'unused', automatic=True))
                report.assert_called_once_with('kun YouTuberについて調べて')

    def test_named_person_routes_to_report(self):
        with patch.object(self.s, 'report', return_value='出典つきの資料') as report:
            self.assertEqual('出典つきの資料', self.s.chat('夏目漱石って誰？', 'unused'))
            report.assert_called_once_with('夏目漱石について調べて')

    def test_cancel_and_topic_switch_clear_pending(self):
        for text in ('キャンセル', '別の話', 'こんにちは', '今日の予定は？'):
            self.s.chat('kunて誰？', 'unused')
            self.s.chat(text, 'unused')
            self.assertIsNone(self.s.pending_person)

    def test_self_question_not_sent_to_research(self):
        with patch.object(self.s, 'report', side_effect=AssertionError('not a person lookup')):
            self.s.chat('あなたは誰？', 'unused')

    def test_explicit_provider_not_rewritten(self):
        with patch.object(self.s, 'report', return_value='指定方法') as report:
            self.s.chat('WikipediaでKUNについて調べて', 'unused')
            report.assert_called_once_with('WikipediaでKUNについて調べて', model='unused')

    def test_real_report_path_no_evidence_no_invented_biography(self):
        self.s.demo = False
        with patch.object(self.s.methods, 'candidates', return_value=([], ['検索結果なし'])):
            answer = self.s.web_chat('夏目漱石は誰ですか？', 'unused', automatic=True)
        self.assertIn('本文根拠を取得できませんでした', answer)
        self.assertNotIn('人物の情報は提供できません', answer)
