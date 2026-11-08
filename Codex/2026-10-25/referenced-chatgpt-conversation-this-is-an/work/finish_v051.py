from pathlib import Path
p=Path('outputs/tomeris_desktop.py');p.write_text(p.read_text(encoding='utf-8-sig').replace('tomeris_desktop_v050','tomeris_desktop_v051'),encoding='utf-8')
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8').replace('起動先：tomeris_desktop_v050.py。290件の自動テストとwork/check_v050_ui.py成功。','起動先：tomeris_desktop_v051.py。295件の自動テスト成功。今回画面変更なし。')
s+='''

## v0.51 最大2テーマの同時取得（ユーザー指定）
ユーザーは複数同時取得を希望。その後「最大50は？」に対し意味確認したが「無視で」と回答したため、50件への拡張はしない。最大2テーマの並行取得を実装。
新規tomeris_parallel_collection.pyでネット読み取りだけを最大2スレッドに分離。結果はテーマごとに保存し、catalogueの書き込みは既存サービスワーカーで順番に行う。片方の取得失敗でももう片方を処理する。1起動最大3試行・停止設定・テーマ上限3件を維持。次のバッチは完了から10分以上。停止操作は従来通り処理終了後に受け付けるため、進行中の通信を即中断する機能ではない。
バリアで2件の取得が同時進行すること、保存が同じスレッドであること、片側失敗、停止、残り1件、合計3試行上限の5件追加。全295件成功。実Wikipedia同時取得・速度改善の実測は未実施（模擬通信）。通常起動v0.51へ反映、旧版・既存データ保持。複数テーマの並行取得であり、同一テーマの複数提供元照合は新規実装していない。
次は前回実Ollama評価で判明した状況分析の具体性不足への改善。既存の評価記録と未使用問題で確認する。
''';p.write_text(s,encoding='utf-8')
