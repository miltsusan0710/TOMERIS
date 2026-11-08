from pathlib import Path
p=Path('outputs/tomeris_desktop.py');p.write_text(p.read_text(encoding='utf-8').replace('tomeris_desktop_v038','tomeris_desktop_v039'),encoding='utf-8')
p=Path('outputs/DEVELOPMENT_NEXT.md');s=p.read_text(encoding='utf-8').replace('起動先：tomeris_desktop_v038.py。210件の自動テスト成功、work/check_v038_ui.py 成功。','起動先：tomeris_desktop_v039.py。216件の自動テスト成功、work/check_v039_ui.py 成功。')
s+='''

## v0.39 ユーザー報告の修正
「今日の予定は？」に架空の運動・読書を回答する問題を修正。tomeris_schedule_grounding.pyが通常会話・自動検索の文脈処理の入口で今日の予定照会を捕捉し、today_plan()の保存済み最新計画と完了状態を直接表示する。未登録・読取失敗を区別し、外部カレンダーを確認していないことも明記。計画作成依頼や明日などの別日を今日の照会へ誤変換しない。Google・天気の確認待ち状態も解除。
一時データで6件追加、計216件成功。GUIから「今日の予定は？」送信も成功。通常起動v0.39へ反映。旧版・既存計画・記憶は変更していない。今日の明示的な予定照会のみ対応し、あらゆる言い換えや任意日付の予定確認への対応は保証しない。
''';p.write_text(s,encoding='utf-8')
