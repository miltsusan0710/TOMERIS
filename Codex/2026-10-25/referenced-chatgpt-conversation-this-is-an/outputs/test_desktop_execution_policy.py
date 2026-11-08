import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from tomeris_execution_policy import important_request,DesktopService,BaseService

class ExecutionPolicyTests(unittest.TestCase):
 def test_important_commands(self):
  for q in ('このメールを送信して','商品を購入して','フォルダを削除して','アクセス権を変更してください'):
   self.assertIsNotNone(important_request(q))
 def test_questions_and_negation_not_commands(self):
  for q in ('メールの送信方法を教えて','フォルダを削除しないで','「商品を購入して」を翻訳して','光合成について説明して'):
   self.assertIsNone(important_request(q))
 def test_no_generated_fake_execution(self):
  with tempfile.TemporaryDirectory() as folder:
   s=DesktopService(Path(folder),demo=True)
   try:
    with patch.object(BaseService,'chat',side_effect=AssertionError('model must not execute')):
     self.assertIn('実行はしていません',s.chat('メールを送信して','unused'))
    with patch.object(BaseService,'web_chat',return_value='通常の検索') as call:
     self.assertEqual(s.web_chat('光合成について知りたい','unused',automatic=True),'通常の検索');call.assert_called_once()
    self.assertIn('事前確認',s.chat('実行方針を教えて','unused'))
   finally:s.close()
