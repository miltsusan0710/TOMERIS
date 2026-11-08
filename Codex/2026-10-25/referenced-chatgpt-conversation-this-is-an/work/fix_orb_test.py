from pathlib import Path
p=Path('outputs/tomeris_orb.py');s=p.read_text(encoding='utf-8-sig').replace('self.after(100,self.tick)','self.tick_job=self.after(100,self.tick)')
s+='''
    def destroy(self):
        for job in (getattr(self,'tick_job',None),self.resize_job):
            if job:
                try:self.after_cancel(job)
                except tk.TclError:pass
        super().destroy()
'''
p.write_text(s,encoding='utf-8')
p=Path('work/check_bright_ui.py');s=p.read_text(encoding='utf-8-sig').replace("'-File','work/capture_tomeris.ps1'","'-ExecutionPolicy','Bypass','-File','work/capture_tomeris.ps1'")
s=s.replace('check=True,capture_output=True','check=True')
p.write_text(s,encoding='utf-8')
