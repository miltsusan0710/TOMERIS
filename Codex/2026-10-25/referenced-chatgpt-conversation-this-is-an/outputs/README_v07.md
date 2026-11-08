# トメリス v0.7：Gemini API追加

v0.6の機能を引き継ぎ、/provider ollama と /provider gemini で切り替えます。既定はOllamaです。複数AIの比較はv0.8で追加します。

## 最初の起動

v0.6を /exit で終了してから、PowerShellで実行してください。

```powershell
Set-Location -LiteralPath 'C:\Users\hiroy\Documents\Codex\2026-10-25\referenced-chatgpt-conversation-this-is-an\outputs'
py -3 -B .\tomeris_v07.py --import-memory .\tomeris_memory_v06.json
```

v0.7専用の tomeris_memory_v07.json を初回だけ作ります。既存の保存先があれば上書きせず停止します。元のv0.6と過去版は変更しません。2回目以降は次を使います。

```powershell
py -3 -B .\tomeris_v07.py
```

## Geminiを設定

1. https://aistudio.google.com/apikey でGoogleの利用条件と利用枠・課金設定を確認し、Gemini APIキーを作成します。
2. トメリスの「あなた >」に /gemini-key と入力します。
3. キー入力欄にAPIキーを貼り付けてEnterを押します。表示されません。キーはこの起動中のRAMだけに保持します。チャットや会話入力欄へキーを書かないでください。
4. /provider gemini と入力します。
5. 「こんにちは。短く自己紹介して」と入力します。
6. Googleへ送る本文が表示されます。内容を確認して yes を入力したときだけ送信します。no で中止します。
7. /provider ollama でローカルAIへ戻せます。/model で現在のAIを確認できます。

環境変数 GEMINI_API_KEY があれば、それも利用できます。/gemini-key の入力値でこの起動中だけ上書きできます。キーの永続保存や自動再送はしません。再起動すると再びOllamaになります。

## 送信・保存の範囲

Geminiへ送るのは公開の固定人格指示と今回の質問だけです。独自の tomeris_core.md、ローカル記憶、成長ログ、知識資料、過去会話、/pcの結果は含めません。そのためGeminiは過去の会話を覚えている前提では回答しません。毎回、本文全体のプレビューと確認を行います。APIキーは認証用ヘッダーだけに入れます。

質問と成功した回答はv0.7のローカル履歴に保存します。キャンセル・通信エラーは保存しません。PC情報は従来どおり画面表示のみです。ユーザーが質問の本文に貼った情報は送信対象になります。

Geminiの回答にも既存の回答検証を適用します。品質基準を満たさないリスク回答は定型回答へ切り替え、追加の自動API呼び出しはしません。Ollamaの再生成動作は従来どおりです。/test はGeminiの場合、キー設定の有無だけを確認し、通信を行いません。

APIエラーでモデルが見つからない場合、利用可能なモデルIDを公式のモデル一覧で確認し、終了後に指定してください。

```powershell
py -3 -B .\tomeris_v07.py --gemini-model gemini-3.5-flash
```

既定IDは gemini-3.5-flash です。利用できるモデルや枠はアカウントとGoogleの提供状況に依存します。HTTP 403はキーの権限・利用条件、404はモデルID、429は利用枠・課金設定を確認してください。エラー本文や認証ヘッダーは表示しません。外部へのリダイレクトと環境変数によるプロキシは無効です。企業ネットワークでプロキシが必須の場合は接続できないことがあります。

## 検証

```powershell
py -3 -B -m unittest discover -s . -p 'test_v07*.py' -v
```

2026-10-25、Windows上で28件成功。新規9件と既存機能の回帰19件です。通信を模擬して、成功・中止・キー未設定・HTTP 429・壊れた応答・出力制限・送信内容の限定・キー非表示・切り替え・記憶とPC取得を確認しました。APIキーを受領していないためGoogleへの実通信は未検証です。

知識フォルダーと人格ファイルはv0.6と共用で読み取ります。記憶JSONはv0.7専用です。v0.7を複数同時起動しないでください。戻す場合は /exit 後に tomeris_v06.py を起動します。

公式資料：
- API形式：https://ai.google.dev/api/generate-content
- キー作成：https://ai.google.dev/gemini-api/docs/api-key
- モデル一覧：https://ai.google.dev/gemini-api/docs/models
