from pathlib import Path
p=Path('outputs/tomeris_desktop.py');p.write_text(p.read_text(encoding='utf-8-sig').replace('tomeris_desktop_v048','tomeris_desktop_v049'),encoding='utf-8')
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8').replace('起動先：tomeris_desktop_v048.py。273件の自動テスト成功。','起動先：tomeris_desktop_v049.py。278件の自動テスト成功。')
s+='''

## v0.49 追加調査と話題切替（項目10完了：対象は定義した言い回し）
優先順位に沿い文脈保持の残件を先行。tomeris_research_boundaries.pyと新GUI v049を追加。「別の話」「別の話にして」「話を変えて」「話題を変えたい」で調査・天気・予定・再調査確認と一時会話文脈を解除。「別の話、計算: 3*4」のような入力は後半を新規質問として処理する。
「他の情報は？」の取得に失敗した後、最後に成功した古い調査対象が引き続き有効になる問題を修正。追加調査で根拠が取れなければ対象・既出URL・出典スナップショットを解除し、次の追加質問には対象を尋ねる。成功した追加調査は既存の対象明示・既出URL除外を維持し、その出典への追質問も新しい取得元のみ表示。
5件の回帰テスト追加、計278件成功。新旧の出典・失敗後の状態・明示話題変更・後半の計算処理を一時データと模擬ページで確認。画面起動・実ネット通信なし、モデルの自由会話全般の理解を保証する変更ではない。通常起動v0.49へ反映し、元の記憶・計画・履歴・旧版を保持。Google/Brave実接続未検証。
次は項目12bの自動収集テーマ編集と状態の一覧。実Ollamaでの固定評価（項目11後半）も未完了。
''';p.write_text(s,encoding='utf-8')
