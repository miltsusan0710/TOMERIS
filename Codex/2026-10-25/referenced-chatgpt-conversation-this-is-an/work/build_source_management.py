from pathlib import Path
s=Path('outputs/tomeris_desktop_v034.py').read_text(encoding='utf-8').replace('v0.34','v0.35').replace('from tomeris_research_learning import','from tomeris_source_management import')
s=s.replace('from tomeris_methods_ui import MethodsPanel','from tomeris_methods_ui import MethodsPanel\nfrom tomeris_sources_ui import SourcesPanel')
s=s.replace('        learning_menu=tk.Menu(menu,tearoff=False)',"        learning_menu=tk.Menu(menu,tearoff=False)\n        learning_menu.add_command(label='保存資料を検索・管理…',command=self.open_sources)")
s=s.replace('    def learning_action(self,question):',"    def open_sources(self):\n        if self.busy or self.closing or self.service is None:return\n        panel=getattr(self,'sources_panel',None)\n        if panel is not None and panel.window.winfo_exists():panel.window.lift();return\n        self.sources_panel=SourcesPanel(self)\n    def learning_action(self,question):")
s=s.replace("        panel=getattr(self,'methods_panel',None)","        panel=getattr(self,'sources_panel',None)\n        if panel is not None:panel.state()\n        panel=getattr(self,'methods_panel',None)")
s=s.replace('                        if not methods_open and',"                        sources_open=getattr(self,'sources_panel',None) and self.sources_panel.window.winfo_exists()\n                        if not sources_open and not methods_open and")
Path('outputs/tomeris_desktop_v035.py').write_text(s,encoding='utf-8')
