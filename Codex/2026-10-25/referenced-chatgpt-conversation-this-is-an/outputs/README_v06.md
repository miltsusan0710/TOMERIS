# トメリス v0.6 導入・検証

添付のv0.5.1を土台に、既存の記憶・検索・成長ログ・回答検証を維持して `/pc` を追加しました。Geminiと回答比較は次のv0.7、v0.8で扱います。

## 新機能と保存の範囲

- `/pc`: OS名・版・構成、論理CPU数、物理メモリー総量・空き・使用率、Python実行ドライブの総容量・空き容量、Python版を取得します。容量の単位はbytesです。
- `--pc-info`: 対話を起動せず同じ情報を表示して終了します。記憶エンジンの初期化もOllama接続も行いません。
- PC情報の取得は標準ライブラリーとWindowsの読み取りAPIのみ。シェル、任意コマンド実行、ファイル内容の読み取り、PC名・ユーザー名・IP・プロセス一覧の収集はありません。
- PC情報は画面だけに表示し、AIへの入力や会話履歴には加えません。自然言語の依頼で自動取得せず、明示的な `/pc` だけで取得します。引数付き `/pc` は拒否します。
- 通常の会話・長期記憶・成長ログは従来どおり保存します。保存先は **tomeris_memory_v06.json** です。PC情報取得の「読み取り専用」はPCの状態を変更しない意味で、アプリ全体の記憶保存を無効にするものではありません。
- 元の **tomeris_memory.json** と過去版は上書きしません。初回の `--import-memory` は指定ファイルの複製を新しい保存先へ作ります。既にv0.6の保存先があれば停止します。複製後の正規化・更新はv0.6のファイルにのみ行われます。
- v0.6とv0.5.1の記憶は以後別々に増えます。同時に複数のv0.6を起動しないでください。共通の記憶エンジンは同時書き込み向けではありません。

## PowerShellで導入

Python 3.10以上が必要です。追加のpipインストールは不要です。以下は作成済みZIPを新しいフォルダーへ展開します。既存フォルダーがあれば停止します。

```powershell
$bundle = 'C:\Users\hiroy\Documents\Codex\2026-10-25\referenced-chatgpt-conversation-this-is-an\outputs\tomeris_v06_bundle.zip'
$installDir = 'C:\Users\hiroy\OneDrive\デスクトップ\tomeris_v06'
if (Test-Path -LiteralPath $installDir) { throw '展開先が既にあります。別の新しいフォルダー名にしてください。' }
Expand-Archive -LiteralPath $bundle -DestinationPath $installDir
Set-Location -LiteralPath $installDir
py -3 --version
py -3 -B .\tomeris_v06.py --pc-info
py -3 -B -m unittest discover -s . -p 'test*.py' -v
```

`py` が使えない環境では、動作しているPython実行ファイルで置き換えてください。`python --version` が使えれば `py -3` を `python` に置換できます。Microsoft Storeの案内だけが出る場合は、実際のPython環境を指定してください。

最初のPC情報表示ではJSON形式の数値が表示され、記憶ファイルは作られません。テストは一時データを使い、既存の本番記憶を読み込みません。19件すべて `OK` になることを確認します。

## 既存記憶を引き継いで起動（初回だけ）

旧アプリを終了してから実行してください。元ファイルのハッシュを前後で比較できます。

```powershell
$oldMemory = 'C:\Users\hiroy\OneDrive\デスクトップ\tomeris_v01\tomeris_memory.json'
$before = (Get-FileHash -LiteralPath $oldMemory -Algorithm SHA256).Hash
py -3 -B .\tomeris_v06.py --import-memory $oldMemory
# 起動後 /memory /memories /pc /quality /exit を順に入力する
$after = (Get-FileHash -LiteralPath $oldMemory -Algorithm SHA256).Hash
if ($before -ne $after) { throw '元の記憶ファイルに変更があります。確認してください。' }
'元の記憶ファイルは変更されていません'
```

`/memory` の保存先が `tomeris_memory_v06.json` であること、`/memories` に既存の長期記憶が表示されることを確認します。2回目以降は以下だけで起動します。

```powershell
py -3 -B .\tomeris_v06.py
```

先に通常起動して空のv0.6記憶ができていた場合、インポートは上書きせず停止します。そのファイルを別名で保管してから再実行してください。

基本人格は既存の `tomeris_core.md` のコピーを同梱しています。知識ファイルは含めていません。必要なら初回導入後に次を実行します。

```powershell
Copy-Item -LiteralPath 'C:\Users\hiroy\OneDrive\デスクトップ\tomeris_v01\knowledge' -Destination .\knowledge -Recurse
```

## Ollamaの会話確認

Ollamaを起動し、既存モデルを確認します。

```powershell
ollama list
```

既定モデルは以前と同じ `qwen2.5:3b` です。存在することを確認して起動後 `/test`、通常の挨拶、`/pc`、`/history` を試します。`/pc` の結果が `/history` に保存されないことを確認してください。未導入モデルを勝手にダウンロードする処理はありません。

通信・回答検証はv0.5.1のプロバイダーとガードレールを引き継いでいます。API形式の参考: https://docs.ollama.com/api/chat 。PC情報をモデルに渡して診断させる機能はこの版にはありません。

## 実施した検証と限界

2026-10-25、Windows上のPythonで19件成功（新規5件とv0.5.1由来14件）。PC情報の実取得、AIへの未送信、履歴への未保存、初回複製と上書き拒否、破損JSON拒否、既存回答検証の回帰を確認しました。テストでは隔離した一時ファイルを使用し、元の記憶データの内容は読み取りませんでした。

Ollamaの11434ポートに応答がなかったため、実モデルの生成とユーザーの本番記憶を使った対話は未検証です。モデル呼び出し部分の回帰テストには模擬応答を使っています。元のフォルダーには変更を加えていません。

取得できないメモリー・ドライブ情報は「取得できません」と表示します。メモリー取得はWindows専用です。CPUは論理プロセッサー数のみで、使用率・温度・GPU診断は対象外です。

戻す場合はv0.6を終了し、以前のフォルダーで従来どおり `py -3 .\tomeris_v051.py` を起動してください。v0.6の新しい記憶を旧版へ自動で統合する処理はありません。
