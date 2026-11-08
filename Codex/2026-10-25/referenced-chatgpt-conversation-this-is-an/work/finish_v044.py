from pathlib import Path
p=Path('outputs/tomeris_desktop.py');p.write_text(p.read_text(encoding='utf-8').replace('tomeris_desktop_v043','tomeris_desktop_v044'),encoding='utf-8')
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8').replace('起動先：tomeris_desktop_v043.py。249件の自動テスト成功。v0.43は既存チャット入力から利用・GUI起動なしでサービス検証。','起動先：tomeris_desktop_v044.py。255件の自動テスト成功。既存チャット入力から利用・GUI起動なしでサービス検証。')
s+='''

## v0.44 履歴からの明示再調査（項目9cのサービス／チャット操作完了）
/research-retry IDで保存質問と選択方法・外部送信を表示し、まだ通信せず確認用トークンを発行。/research-confirm TOKENの明示入力時のみ新規調査する。確認は5分・1回限り。取消・別話題・履歴削除／変更で無効。保存した本文や以前のURLを新しい結果として返さず、取得失敗ならそのまま未確認。新規成功のみ新たな履歴を追加し、以前の履歴は保持（最大100件）。Google等の非対応方法・曖昧な方法・質問の明示方法との不一致は再調査を拒否。
新規tomeris_research_history_v044.pyで報告後に復元された設定を誤って記録する点も修正し、実行前の明示指定／確認待ち／選択設定の順で記録。実提供元の全フォールバック経路のログではない。v043の旧履歴に方法不一致があれば再調査を拒否し、推測で修復しない。
6件追加で全255件成功。確認段階で通信しない、新規ページ取得、失敗時に旧URLを返さない、取消・失効・削除・方法不一致を一時データ・模擬通信で確認。画面起動なし、Google/Brave実キー接続未検証。通常起動v0.44。旧版と本番記憶・計画は保持。
次回：項目9dの履歴一覧画面（最大100件・検索・詳細・選択削除・再調査確認）を作り、長いIDを打たずに使えるようにする。サービスのreview/confirm機能は今回のコードを再利用し、履歴データを勝手に外部へ送らない。項目10残りは継続。
''';p.write_text(s,encoding='utf-8')
