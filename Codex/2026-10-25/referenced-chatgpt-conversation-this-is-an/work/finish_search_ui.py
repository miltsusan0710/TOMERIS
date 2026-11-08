from pathlib import Path
p=Path('outputs/tomeris_history_search_ui.py')
s=p.read_text(encoding='utf-8-sig').replace('ttk.Entry(bar,textvariable=self.query)','ttk.Entry(bar,textvariable=self.query,width=1)')
s=s.replace('                self.result=value','                self.result=value\n                self.query.set(value["query"])')
p.write_text(s,encoding='utf-8')
