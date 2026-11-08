from pathlib import Path
p=Path('outputs/tomeris_desktop_v030.py');s=p.read_text(encoding='utf-8')
s=s.replace("        compact=event.height<800\n        self.orb.configure(height=84 if compact else 150)", "        compact=event.height<900\n        dense=float(self.root.tk.call('tk','scaling'))>2 and compact\n        self.orb.configure(height=48 if dense else (84 if compact else 150))\n        if dense:self.connection_label.grid_remove()\n        else:self.connection_label.grid()")
p.write_text(s,encoding='utf-8')
p=Path('work/check_hud_layout.py');s=p.read_text(encoding='utf-8-sig').replace("print('scale',scale,'transcript',app.transcript.winfo_height(),flush=True)","assert app.transcript.winfo_height()>140, (scale,app.transcript.winfo_height())");p.write_text(s,encoding='utf-8')
