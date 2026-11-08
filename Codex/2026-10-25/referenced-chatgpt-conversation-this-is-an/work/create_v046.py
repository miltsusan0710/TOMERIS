from pathlib import Path
p=Path('outputs');s=(p/'tomeris_desktop_v045.py').read_text(encoding='utf-8').replace('v0.45','v0.46')
s=s.replace('from tomeris_sources_ui import SourcesPanel','from tomeris_sources_ui import SourcesPanel\nfrom tomeris_research_history_ui import ResearchHistoryPanel')
s=s.replace("menu.add_cascade(label='資料学習',menu=learning_menu)","learning_menu.add_command(label='調査履歴を見る・再調査',command=self.open_research_history)\n        menu.add_cascade(label='資料学習',menu=learning_menu)")
pos=s.index('    def control_state(self):')
s=s[:pos]+'''    def open_research_history(self):
        if self.busy or self.closing:return
        panel=getattr(self,'research_history_panel',None)
        if panel and panel.window.winfo_exists():panel.window.lift();return
        self.research_history_panel=ResearchHistoryPanel(self)

'''+s[pos:]
s=s.replace('    def control_state(self):','    def control_state(self):\n        research_panel=getattr(self,"research_history_panel",None)\n        if research_panel:research_panel.state()',1)
(p/'tomeris_desktop_v046.py').write_text(s,encoding='utf-8')
