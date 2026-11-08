import sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v015 import TomerisWindow

def wait(root,app):
    limit=time.monotonic()+8
    while app.busy and time.monotonic()<limit:
        root.update(); time.sleep(.02)
    assert not app.busy

for scale in [1.333333,2.0,2.666667]:
    with tempfile.TemporaryDirectory(dir='work/v07') as folder:
        root=tk.Tk(); root.withdraw(); root.tk.call('tk','scaling',scale)
        app=TomerisWindow(root,data_dir=Path(folder),demo=True); wait(root,app)
        root.deiconify(); app.view('plan_history'); panel=app.plan_history_panel; wait(root,app)
        for size in ['800x650','600x500']:
            panel.window.geometry(size); root.update()
            for button in [panel.carry_button,panel.exit_button,panel.reflect_button,panel.weekly_button]:
                x=button.winfo_rootx()-panel.window.winfo_rootx()
                y=button.winfo_rooty()-panel.window.winfo_rooty()
                assert x>=0 and y>=0 and x+button.winfo_width()<=panel.window.winfo_width() and y+button.winfo_height()<=panel.window.winfo_height(),(scale,size,x,y,button.winfo_width(),button.winfo_height(),panel.window.winfo_width(),panel.window.winfo_height())
            assert panel.detail.winfo_height()>1,(scale,size,'no detail area')
        panel.close(); app.close()
        limit=time.monotonic()+8
        while time.monotonic()<limit:
            try:
                root.update()
                if not root.winfo_exists(): break
            except tk.TclError: break
            time.sleep(.02)
        else: raise AssertionError('close failed')
print('Layout bounds: both buttons visible at 100%, 150%, 200% (800x650 and 600x500)')



