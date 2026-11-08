from pathlib import Path
p=Path('outputs/tomeris_sources_ui.py');s=p.read_text(encoding='utf-8-sig').replace('from tkinter import ttk,messagebox','from tkinter import ttk,messagebox,font')
s=s.replace("        self.tree=ttk.Treeview(listing,columns", "        tree_font=font.Font(self.window,family='Yu Gothic UI',size=10)\n        ttk.Style(self.window).configure('Sources.Treeview',font=tree_font,rowheight=tree_font.metrics('linespace')+8)\n        self.tree_font=tree_font\n        self.tree=ttk.Treeview(listing,style='Sources.Treeview',columns")
p.write_text(s,encoding='utf-8')
