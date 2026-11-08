from pathlib import Path
p=Path('outputs/tomeris_research_history_ui.py');s=p.read_text(encoding='utf-8').replace("entry.grid(row=0,column=0,sticky='ew');self.query", "entry.grid(row=0,column=0,sticky='ew');self.entry=entry;self.query").replace('(self.reload,self.retry,self.delete,self.exit,self.list)', '(self.reload,self.retry,self.delete,self.exit,self.list,self.entry)')
p.write_text(s,encoding='utf-8')
