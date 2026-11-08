from pathlib import Path
root=Path('outputs')
s=(root/'tomeris_desktop_v015.py').read_text(encoding='utf-8-sig').replace('v0.15','v0.16')
s=s.replace('from tkinter import ttk, messagebox','from tkinter import ttk, messagebox, filedialog\nfrom datetime import datetime')
s=s.replace('from tomeris_weekly import DesktopService as PlanService','from tomeris_backup import DesktopService as PlanService')
s=s.replace('    def make_ui(self):', "    def make_ui(self):\n        menu=tk.Menu(self.root)\n        self.data_menu=tk.Menu(menu,tearoff=False)\n        self.data_menu.add_command(label='記憶・計画のバックアップを保存…',command=self.backup)\n        menu.add_cascade(label='データ',menu=self.data_menu)\n        self.root.configure(menu=menu)")
s=s.replace("        active=not self.busy and not self.closing and self.service is not None", "        active=not self.busy and not self.closing and self.service is not None\n        self.data_menu.entryconfigure(0,state='normal' if active else 'disabled')")
s=s.replace('    def open_google(self):', "    def backup(self):\n        if self.busy or self.closing: return\n        path=filedialog.asksaveasfilename(parent=self.root,title='記憶・計画のバックアップ（個人の記録を含むZIP）',\n            defaultextension='.zip',initialfile='tomeris_backup_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.zip',\n            filetypes=[('ZIPファイル','*.zip')])\n        if path:\n            self.submit('reply',lambda:self.service.export_backup(path),'バックアップを作成・確認しています…')\n    def open_google(self):")
(root/'tomeris_desktop_v016.py').write_text(s,encoding='utf-8')
