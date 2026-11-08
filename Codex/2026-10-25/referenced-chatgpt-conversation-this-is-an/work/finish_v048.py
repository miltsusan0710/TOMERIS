from pathlib import Path
p=Path('outputs/tomeris_desktop.py');p.write_text(p.read_text(encoding='utf-8').replace('tomeris_desktop_v047','tomeris_desktop_v048'),encoding='utf-8')
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8').replace('起動先：tomeris_desktop_v047.py。267件の自動テストとwork/check_v047_ui.py成功。','起動先：tomeris_desktop_v048.py。273件の自動テスト成功。今回画面変更なし・GUI起動なし。')
s+='''

## v0.48 自動資料収集の停止設定を保存（項目12a完了）
新規tomeris_collection_settings.pyでauto_collection.jsonの有効／停止を原子的に保存・次回起動へ引き継ぐ。初回（設定ファイルなし）は従来通り有効。読取失敗・形式不正・容量超過では停止し、破損ファイルを上書きしない。停止の保存に失敗しても現在のプロセスは即停止、次回設定が保存できなかったことを明記。再開成功時は最低10分待機し即通信を避ける。試行数と3固定テーマは引き続き各起動中の仕様。
backup_v048/restore_v048に設定ファイル・4KB制限・共通検証を追加。停止設定のZIP復元後も停止すること、旧ZIP互換を検証。新GUI v048から使用、旧版保持。再起動継承・不正設定・保存失敗・再開間隔・バックアップ復元の6件追加で計273件成功。画面起動なし、実ネット通信なし、有効APIキー実接続未検証。本番の設定や記憶・計画は変更せず通常起動だけv0.48へ反映。
次は項目12b：テーマを確認して編集できる設定画面・収集結果の一覧。現行は固定3テーマのまま。項目10の文脈範囲と実モデル評価も未完了。
''';p.write_text(s,encoding='utf-8')
