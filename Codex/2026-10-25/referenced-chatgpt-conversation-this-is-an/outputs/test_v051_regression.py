import contextlib
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import tomeris_v06 as app
import tomeris_guardrails as guards
from tomeris_memory_engine import MemoryStore


SAMPLE_V05_BAD = '''**リスク1: 他人の財産や情報へのアクセスのリスク**
- **リスク**: 他人のPCに不正アクセスを試みる可能性があります。
- **起こり得る影響**: 財産が盗まれる可能性があります。
- **対策**: ユーザーの許可を得ない限り、PC操作の機能は使用しない。
- **実行前の確認事項**: ユーザーの許可を得た後、許可が必要となる。

**リスク2: プライバシー侵害**
- **リスク**: 個人情報にアクセスする可能性があります。
- **影響**: プライバシーが侵害されます。
- **対策**: ユーザーの許可を得ない限り、PC操作の機能は使用しない。
- **実行前の確認事項**: ユーザーの許可を得た後、許可が必要となる。

**リスク3: セキュリティリスク**
- **リスク**: PCにサイバー攻撃が起こります。
- **影響**: 情報が危険にさらされます。
- **対策**: ユーザーの許可を得ない限り、PC操作の機能は使用しない。
- **実行前の確認事項**: ユーザーの許可を得た後、許可が必要となる。

これらのリスクを考慮し、PC操作機能の追加を実行する'''
QUESTION = 'トメリスにPC操作機能を追加する場合、長期的な勝利という方針に基づいて、優先的に対処すべきリスクを3つ挙げてください。'


class V051GuardrailTests(unittest.TestCase):
    def make_store(self, folder):
        return MemoryStore(Path(folder) / 'temp_memory.json', Path(folder) / 'knowledge')

    def test_bad_v05_answer_is_rejected(self):
        issues = guards.review_pc_risk_answer(QUESTION, SAMPLE_V05_BAD)
        self.assertTrue(any('一般論' in x for x in issues))
        self.assertTrue(any('実行を宣言' in x for x in issues))
        self.assertTrue(any('具体的' in x for x in issues))

    def test_fallback_has_three_distinct_concrete_risks(self):
        answer = guards.pc_risk_fallback(QUESTION)
        self.assertEqual([], guards.review_pc_risk_answer(QUESTION, answer))
        self.assertIn('ファイルの誤削除', answer)
        self.assertIn('機密情報の漏えい', answer)
        self.assertIn('指示の誤解', answer)
        self.assertIn('未実行', answer)  # operational status must be explicit

    def test_fallback_respects_requested_one_and_five(self):
        for count in (1, 2, 4, 5):
            q = f'PC操作機能についてリスクを{count}つ挙げて'
            self.assertEqual(count, guards.requested_risk_count(q))
            self.assertEqual([], guards.review_pc_risk_answer(q, guards.pc_risk_fallback(q)))

    def test_retry_then_safe_fallback_if_bad_twice(self):
        with TemporaryDirectory() as folder:
            store = self.make_store(folder)
            provider = Mock()
            provider.generate.side_effect = [SAMPLE_V05_BAD, SAMPLE_V05_BAD]
            result = app.generate_checked_response(provider, store, QUESTION)
            self.assertIn('定型回答に切り替え', result)
            self.assertEqual(2, provider.generate.call_count)
            self.assertEqual([], guards.review_pc_risk_answer(QUESTION, result))
            retry_messages = provider.generate.call_args.args[0]
            self.assertTrue(any('再作成' in x['content'] for x in retry_messages))

    def test_retry_then_accepts_improved_response(self):
        with TemporaryDirectory() as folder:
            store = self.make_store(folder)
            provider = Mock()
            valid = guards.pc_risk_fallback(QUESTION)
            provider.generate.side_effect = [SAMPLE_V05_BAD, valid]
            result = app.generate_checked_response(provider, store, QUESTION)
            self.assertTrue(result.endswith(valid))
            self.assertTrue(result.startswith('【操作状態：未実行'))
            self.assertEqual(2, provider.generate.call_count)

    def test_no_retry_when_answer_is_good(self):
        with TemporaryDirectory() as folder:
            store = self.make_store(folder)
            provider = Mock()
            provider.generate.return_value = guards.pc_risk_fallback(QUESTION)
            app.generate_checked_response(provider, store, QUESTION)
            self.assertEqual(1, provider.generate.call_count)

    def test_direct_pc_operation_is_not_forwarded_to_model(self):
        with TemporaryDirectory() as folder:
            store = self.make_store(folder)
            provider = Mock()
            result = app.generate_checked_response(provider, store, 'PCの重要なファイルを削除して')
            provider.generate.assert_not_called()
            self.assertIn('未実行', result)

    def test_nonrisk_falsely_completed_action_is_suppressed(self):
        with TemporaryDirectory() as folder:
            store = self.make_store(folder)
            provider = Mock()
            provider.generate.return_value = 'PCのファイル削除を実行しました。'
            result = app.generate_checked_response(provider, store, 'PC操作の基本を説明して')
            self.assertIn('未実行', result)
            self.assertNotIn('実行しました', result)

    def test_general_question_still_uses_ollama_answer(self):
        with TemporaryDirectory() as folder:
            store = self.make_store(folder)
            provider = Mock()
            provider.generate.return_value = '3つのポイントを説明します。'
            result = app.generate_checked_response(provider, store, '整理するコツは？')
            self.assertEqual('3つのポイントを説明します。', result)

    def test_quality_command_does_not_call_model(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            with patch.object(app, 'MEMORY_FILE', root/'memory.json'), \
                 patch.object(app, 'KNOWLEDGE_DIR', root/'knowledge'), \
                 patch.object(app, 'CORE_FILE', root/'core.md'), \
                 patch.object(app.OllamaProvider,'check',return_value=(True,'offline mock')), \
                 patch.object(app.OllamaProvider,'generate',side_effect=AssertionError('AI should not be called')):
                out=io.StringIO()
                with patch('builtins.input',side_effect=['/quality','/safety','/exit']), contextlib.redirect_stdout(out):
                    self.assertEqual(0, app.main())
            self.assertIn('形式・キーワード', out.getvalue())
            self.assertIn('初期設定は読み取り専用', out.getvalue())

    def test_existing_memory_remains_when_app_exits(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            store=self.make_store(folder)
            store.add_memory('目標', '長期的な勝利', 'トメリス', 5)
            with patch.object(app,'MEMORY_FILE',root/'temp_memory.json'), \
                 patch.object(app,'KNOWLEDGE_DIR',root/'knowledge'), \
                 patch.object(app,'CORE_FILE',root/'core.md'), \
                 patch.object(app.OllamaProvider,'check',return_value=(True,'offline mock')):
                with patch('builtins.input',side_effect=['/memories','/exit']),contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(0, app.main())
            reloaded=self.make_store(folder)
            self.assertEqual('長期的な勝利', reloaded.data['memories'][0]['text'])

    def test_cli_replaces_bad_model_output_and_records_only_checked_answer(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            memory_path = root / 'memory.json'
            with patch.object(app, 'MEMORY_FILE', memory_path), \
                 patch.object(app, 'KNOWLEDGE_DIR', root / 'knowledge'), \
                 patch.object(app, 'CORE_FILE', root / 'core.md'), \
                 patch.object(app.OllamaProvider, 'check', return_value=(True, 'offline mock')), \
                 patch.object(app.OllamaProvider, 'generate', side_effect=[SAMPLE_V05_BAD, SAMPLE_V05_BAD]):
                out = io.StringIO()
                with patch('builtins.input', side_effect=[QUESTION, '/exit']), contextlib.redirect_stdout(out):
                    self.assertEqual(0, app.main())
            self.assertIn('定型回答に切り替え', out.getvalue())
            self.assertNotIn('追加を実行する', out.getvalue())
            saved = MemoryStore(memory_path, root / 'knowledge').recent_conversations(limit=1)[0]['tomeris']
            self.assertIn('操作状態：未実行', saved)
            self.assertNotIn('追加を実行する', saved)

    def test_provider_failure_does_not_get_saved_as_conversation(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            memory_path = root / 'memory.json'
            with patch.object(app, 'MEMORY_FILE', memory_path), \
                 patch.object(app, 'KNOWLEDGE_DIR', root / 'knowledge'), \
                 patch.object(app, 'CORE_FILE', root / 'core.md'), \
                 patch.object(app.OllamaProvider, 'check', return_value=(False, 'offline mock')), \
                 patch.object(app.OllamaProvider, 'generate', side_effect=app.ProviderError('offline test')):
                with patch('builtins.input', side_effect=['挨拶して', '/exit']), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(0, app.main())
            store = MemoryStore(memory_path, root / 'knowledge')
            self.assertEqual(0, store.stats()['conversations'])

    def test_risk_question_detection(self):
        self.assertTrue(guards.is_pc_risk_question(QUESTION))
        self.assertFalse(guards.is_pc_risk_question('PCのファイルを削除して'))
        self.assertTrue(guards.is_direct_pc_action_request('このフォルダを削除して'))
        self.assertFalse(guards.is_direct_pc_action_request('フォルダを削除する前に確認すべきリスクは？'))


if __name__ == '__main__':
    unittest.main()
