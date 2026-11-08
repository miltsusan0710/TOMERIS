import unittest
from unittest.mock import Mock
from tomeris_language_actions import action_for,perform
from tomeris_desktop_v070 import TomerisWindow

class LanguageActionTests(unittest.TestCase):
 def test_variations(self):
  for text,expected in [('トメリス、今日の予定を見せて。','today'),('保存した資料を開いて','sources'),('記憶を確認したい','memories'),('画像を見て','image'),('今の返事を読み上げて','speak'),('会話設定を開いて','settings'),('ＰＣの情報を見せて','pc')]:
   self.assertEqual(action_for(text),expected)
 def test_no_partial_or_negative_commands(self):
  for text in ['設定を開かないで','「画像を見て」と言われた','予定を削除して','メールを送信して','画像を見てからファイルを削除','この資料を開いていいか悩んでいる']:
   self.assertIsNone(action_for(text))
 def test_reading_does_not_generate_an_answer(self):
  app=Mock();perform(app,'today');app.view.assert_called_once_with('today');app.service.chat.assert_not_called()
 def test_settings_always_opens_not_toggles(self):
  app=Mock();perform(app,'settings');perform(app,'settings');self.assertEqual(app.show_chat_settings.set.call_args.args,(True,))
 def test_send_routes_recognized_text_to_existing_action(self):
  app=Mock();app.busy=False;app.closing=False;app.entry.get.return_value='今日の予定を見せて'
  self.assertEqual(TomerisWindow.send(app),'break');app.view.assert_called_once_with('today');app.submit.assert_not_called();app.entry.delete.assert_called_once()
 def test_empty_reading_notice(self):
  app=Mock();app.last_answer=None;perform(app,'speak');app.append.assert_called_once()
