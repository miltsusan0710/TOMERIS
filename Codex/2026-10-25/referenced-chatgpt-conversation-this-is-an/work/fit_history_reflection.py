from pathlib import Path
p=Path('outputs/tomeris_plan_history_ui_v014.py')
s=p.read_text(encoding='utf-8-sig').replace('height=5,width=1','height=3,width=1')
s=s.replace("f'{len(self.visible)}件の計画。日付と保存順で新しいものから表示しています。閲覧では記録を変更しません。'", "f'{len(self.visible)}件。新しい順に表示しています。計画を選んでください。'")
p.write_text(s,encoding='utf-8')
