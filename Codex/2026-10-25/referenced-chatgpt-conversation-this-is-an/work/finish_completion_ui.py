from pathlib import Path
p=Path('outputs/tomeris_today_ui.py')
s=p.read_text(encoding='utf-8-sig').replace("geometry('650x470'); self.window.minsize(560,420)","geometry('700x650'); self.window.minsize(620,600)")
s=s.replace("        plan=snapshot['plan']", "        plan=snapshot['plan']\n        goal=plan['goal'] if len(plan['goal'])<=120 else plan['goal'][:120]+'…'")
s=s.replace("\\n{plan['goal']}","\\n{goal}")
p.write_text(s,encoding='utf-8')
