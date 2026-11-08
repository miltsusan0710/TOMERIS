from pathlib import Path
p=Path('outputs/tomeris_desktop.py');p.write_text(p.read_text(encoding='utf-8').replace('tomeris_desktop_v045','tomeris_desktop_v046'),encoding='utf-8')
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8').replace('起動先：tomeris_desktop_v045.py。261件の自動テスト成功。既存チャット入力から利用・GUI起動なしでサービス検証。','起動先：tomeris_desktop_v046.py。261件の自動テストとwork/check_v046_ui.py成功。')
s+='''

## v0.46 調査履歴一覧画面（項目9d完了）
「資料学習」メニューに「調査履歴を見る・再調査」を追加。最大100件を一覧表示し、質問・方法・出典名・URLを検索できる。詳細は過去の記録・未再取得と明記。個別削除は質問を表示して確認。再調査はサービスの確認トークンを再利用し、質問・方法・外部送信をダイアログで確認してから実行。取消では通信なし。結果は会話欄へ表示。読み書き・再調査は既存の単一ワーカーで行い、処理中の操作を無効化。
旧版・データを保持し、新GUI v046とtomeris_research_history_ui.pyを追加。261件回帰テスト成功。一時データのテスト画面だけ短時間起動し、絞り込み・過去表示・再調査取消・明示確認後の模擬取得・個別削除を確認（work/check_v046_ui.py）。ユーザーの普段のトメリスや本番データは使用せず、外部実通信なし。APIキー実接続未検証。通常起動v0.46へ反映。
項目9の保存・閲覧・削除・明示再調査・バックアップは完了。方法欄は選択設定のみで、実提供元の全フォールバック経路を監査記録する機能は未実装。次は項目10の残り：追加調査の対象・範囲を明示し、別話題／失敗後の古い根拠への戻りを横断テストする。
''';p.write_text(s,encoding='utf-8')
