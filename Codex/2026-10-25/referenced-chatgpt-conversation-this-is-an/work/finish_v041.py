from pathlib import Path
p=Path('outputs/tomeris_desktop.py');p.write_text(p.read_text(encoding='utf-8').replace('tomeris_desktop_v040','tomeris_desktop_v041'),encoding='utf-8')
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8').replace('起動先：tomeris_desktop_v040.py。222件の自動テスト成功、work/check_v040_ui.py 成功。','起動先：tomeris_desktop_v041.py。229件の自動テスト成功、work/check_v041_ui.py 成功。').replace('8. 【次】','8. 【完了 v0.41】').replace('9. 【未完了】','9. 【次】')
s+='''

## v0.41 継続実行結果
計画履歴に「残った行動を明日の下書きに」を追加。今日以前の各日の最新改訂から、完了チェック済みを除いた行動を準備。チェック記録がない場合は未完了と断定せず注意文を表示。確認画面に明日の日付・対象日の既存計画有無を示し、各行動を選択して明示保存する。元の計画も対象日にあった計画も履歴へ保持。対象日は明日固定（任意未来日は未対応）。既存save_planの今日限定制約は維持。
保存前に計画・完了記録の変更と日付変更を検査。下書きトークンの再使用・同内容の重複保存・空選択を拒否。保存失敗時は元ファイル保持。既存daily_plans.json形式なのでバックアップ対象は従来通り。
7件の回帰テスト追加、計229件成功。UIテストで下書き表示→確認→保存→2件の履歴保持まで一時データで確認。実際のユーザーの計画を変更したり自動で翌日へ移したりしていない。新規tomeris_tomorrow_plans.py、tomeris_tomorrow_ui.py、GUI v041を追加、旧版を保持して通常起動をv0.41へ変更。次は項目9の調査履歴。複数アプリ同時起動によるファイル競合は完全な排他制御をしていないため今後の改善候補。
''';p.write_text(s,encoding='utf-8')
