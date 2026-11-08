from pathlib import Path
p=Path('outputs/tomeris_desktop.py');p.write_text(p.read_text(encoding='utf-8-sig').replace('tomeris_desktop_v049','tomeris_desktop_v050'),encoding='utf-8')
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8').replace('起動先：tomeris_desktop_v049.py。278件の自動テスト成功。今回画面変更なし・GUI起動なし。','起動先：tomeris_desktop_v050.py。290件の自動テストとwork/check_v050_ui.py成功。')
s+='''

## v0.50 自動収集テーマの編集・状態画面（項目12b完了）
資料学習メニューに「自動収集のテーマ・結果」を追加。保存済みの1〜3テーマを編集し、外部へ送信する対象名を確認して保存。保存前に停止設定を永続化し、保存成功後も停止を維持。別途「再開」で確認して最低10分後に収集。編集で1起動3試行の上限はリセットしない。テーマはWikipediaの同名記事のみを対象とし、任意リンク巡回はしない。
起動中のテーマごとの保存／失敗結果を一覧表示。取得内容は未検証でありモデル能力向上とは表示しない。テーマ不正ファイルは保持して停止、再開拒否。テーマ保存失敗でも停止を維持。新規backup_v050/restore_v050はauto_topics.jsonを4KB上限・共通検証で保存復元する。復元後の停止・編集テーマ保持を検証。
5件追加で全290件成功。一時データの短時間UIで保存取消・確認・停止保持・明示再開を確認（work/check_v050_ui.py）。実ネットやAPIキー接続は未検証。新GUI v050と関連モジュール追加、旧版・本番記憶・計画・設定は保持。通常起動v0.50へ反映。
残件は項目11後半：実Ollamaの固定評価で会話・状況分析の回答を記録する。オフライン10問の成功を理解力向上と混同せず、事前に定めた基準で結果と不足を説明する。現在の3試行上限・同名記事のみの取得では一般Webの網羅的収集にはならない。
''';p.write_text(s,encoding='utf-8')
