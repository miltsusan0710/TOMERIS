# トメリス v0.10：Googleカレンダー（読み取り専用）

既存のトメリスを閉じ、デスクトップのアイコンから開き直してください。
画面右上に「Googleカレンダー」が増えています。「初回設定の手順」でGoogle側の設定を案内します。
Pythonの追加ライブラリは不要です。従来の会話・記憶・計画は引き続き利用できます。

## 今回の範囲

- 複数アカウントの追加、再接続、選択、全アカウント表示、ローカル登録削除。
- Google上で表示対象のカレンダーについて、日本時間の今日の予定を取得。
- 終日予定、日をまたぐ予定、繰り返し予定、複数ページ、アカウントごとの取得失敗に対応。
- GoogleカレンダーへのAPI呼び出しはGETのみ。Gmail、予定編集、AI要約は今回未実装。
- 予定は専用画面だけに表示し、会話履歴・長期記憶・計画ファイルには保存しません。
- 設定と認証情報は `tomeris_desktop_data/google_connection.dpapi` にWindows DPAPIで暗号化保存。
- アカウントの識別はGoogleの固定IDを使用。画面にはメールアドレスを表示。
- システムブラウザー、127.0.0.1の一時ポート、state検証、PKCEを使って接続。
- 認証コードやトークンをログへ出力しません。Googleから返されたエラー本文もそのまま表示しません。
- 接続情報を削除してもGoogle側の許可は残ります。完全な解除はGoogleアカウントの接続管理で行います。

## 実装と旧版

起動用 `tomeris_desktop.py` はv0.10を呼び出します。既存ショートカットの変更は不要。
v0.9.1の画面は `tomeris_desktop_v091.py` に残っています。

旧版へ戻して起動する場合、アプリを閉じてからPowerShellで：

```powershell
Set-Location -LiteralPath 'C:\Users\hiroy\Documents\Codex\2026-10-25\referenced-chatgpt-conversation-this-is-an\outputs'
py -3 -B .\tomeris_desktop_v091.py
```

Googleの認証JSONはご本人がGoogle Cloudで作成する必要があります。アプリのヘルプに詳しい手順があります。
外部・テスト設定では通常7日後に再接続が必要です。個人利用向けの初期実装であり、一般公開の審査完了を意味しません。

## 検証

27件の自動テストが成功（従来機能12件＋Google機能15件）。
実Windows DPAPI暗号化・復号、認証情報の分離、更新、保存失敗時の保護、権限制限、認証stateとPKCE、ページ取得、日本時間への変換、アカウント単位の部分失敗を検証しました。
追加の起動テストで、Google設定画面・未登録表示・通常の記憶を変更しないこと・終了を確認。
PC内の一時HTTPサーバーを実際に使い、擬似ブラウザーからの認証コールバックと中止を検証しました。
実アカウントによるGoogle認証・実予定の取得は、本人の設定と許可が未実施のため未検証です。

公式資料：
- https://developers.google.com/identity/protocols/oauth2/native-app
- https://developers.google.com/workspace/calendar/api/quickstart/python
- https://developers.google.com/workspace/calendar/api/v3/reference/events/list
- https://developers.google.com/workspace/calendar/api/v3/reference/calendarList/list
- https://developers.google.com/workspace/guides/configure-oauth-consent
