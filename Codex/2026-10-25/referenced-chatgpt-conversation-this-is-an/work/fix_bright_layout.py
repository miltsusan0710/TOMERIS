from pathlib import Path
p=Path('outputs/tomeris_desktop_v025.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace("main.bind('<Configure>',lambda event:self.status_label.configure(wraplength=max(250,event.width-8)))","main.bind('<Configure>',self.fit_chat_layout)")
s=s.replace('    def change_text_size(self,delta):',"    def fit_chat_layout(self,event):\n        compact=event.height<800\n        self.orb.configure(height=60 if compact else 120)\n        self.entry.configure(height=2 if compact else 3)\n        self.status_label.configure(wraplength=max(250,event.width-8))\n    def change_text_size(self,delta):")
s=s.replace('    root=tk.Tk()','    try:\n        import ctypes\n        ctypes.windll.user32.SetProcessDPIAware()\n    except (AttributeError,OSError):\n        pass\n    root=tk.Tk()')
p.write_text(s,encoding='utf-8')
p=Path('work/check_bright_ui.py');s=p.read_text(encoding='utf-8-sig').replace('import subprocess','import subprocess\nimport ctypes\nctypes.windll.user32.SetProcessDPIAware()')
s=s.replace("root.update();time.sleep(.15);root.update()","root.update();time.sleep(.15);root.update();app.transcript.see('1.0');root.update()")
p.write_text(s,encoding='utf-8')
