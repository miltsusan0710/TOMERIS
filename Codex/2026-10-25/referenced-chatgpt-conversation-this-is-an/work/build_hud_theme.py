from pathlib import Path
s=Path('outputs/tomeris_desktop_v029.py').read_text(encoding='utf-8')
s=s.replace('from tomeris_orb import Orb','from tomeris_hud_orb import Orb').replace('v0.29','v0.30')
colors={'#eef2f5':'#08131f','#edf5f8':'#08131f','#f8fbfc':'#0c1c2b','#dce8ed':'#214655','#254d5d':'#67e5f5','#617b88':'#9ab5c7','#355461':'#c1dce8','#dfeff4':'#173b4c','#173e50':'#9cf4ff','#9babb3':'#718b9d','#ffffff':'#102536','#284c5b':'#dceff6','#cfdee5':'#295265','#edf3f6':'#10202d','#e5eff4':'#183647','#e4f2f6':'#204b60','#899ca6':'#718b9d','#e4eef3':'#183647','#496573':'#b4ccd8','#58727f':'#9ab5c7','#d3e2e9':'#295265','#244859':'#67e5f5','#253e4b':'#e1eef5','#23647e':'#a2ecfa','#edf6fa':'#19374a','#214957':'#67e5f5','#677b86':'#a7bdcc','#287e98':'#51d5e9','#aecbd7':'#295265','#328da6':'#68edff','#1d667e':'#8aedfa','#c1d7e1':'#456777','#526d7a':'#9ab5c7','#006aaa':'#7ddfff'}
for a,b in colors.items():s=s.replace(a,b)
s=s.replace("fg='#102536',activebackground='#8aedfa',activeforeground='#102536'", "fg='#071923',activebackground='#8aedfa',activeforeground='#071923'")
s=s.replace("text='思考を、次の行動へ。'", "text='PERSONAL ASSISTANT'")
s=s.replace("text='会話',bg=", "text='会話  /  COMMUNICATION',bg=")
s=s.replace("actions=ttk.Frame(side)","style.configure('Side.TFrame',background='#0c1c2b')\n        actions=ttk.Frame(side,style='Side.TFrame')")
s=s.replace("self.transcript.grid(row=1", "self.transcript.configure(selectbackground='#2c6177',selectforeground='#ffffff',insertbackground='#67e5f5')\n        self.transcript.vbar.configure(background='#183647',troughcolor='#102536',activebackground='#32778e')\n        self.transcript.grid(row=1")
s=s.replace("self.entry.grid(row=2", "self.entry.configure(selectbackground='#2c6177',selectforeground='#ffffff')\n        self.entry.grid(row=2")
s=s.replace("self.orb.configure(height=60 if compact else 120)","self.orb.configure(height=84 if compact else 150)")
# Keep popup lists legible; native auxiliary dialogs retain their existing light surfaces.
s=s.replace("style=ttk.Style();style.theme_use('clam')", "style=ttk.Style();style.theme_use('clam')\n        self.root.option_add('*TCombobox*Listbox.background','#102536')\n        self.root.option_add('*TCombobox*Listbox.foreground','#e1eef5')\n        self.root.option_add('*TCombobox*Listbox.selectBackground','#28617a')\n        self.root.option_add('*TCombobox*Listbox.selectForeground','#ffffff')")
Path('outputs/tomeris_desktop_v030.py').write_text(s,encoding='utf-8')
