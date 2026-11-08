import sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v015 import TomerisWindow
from tomeris_weekly import DesktopService,today

def wait(root,app):
    limit=time.monotonic()+8
    while app.busy and time.monotonic()<limit:
        root.update(); time.sleep(.02)
    assert not app.busy
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    service=DesktopService(folder,demo=True)
    service.save_plan('今週の確認',10,[{'title':'記録を見る','minutes':5}],today())
    state=service.today_plan(); service.set_completion(state['id'],0,True)
    service.save_reflection(state['id'],'落ち着いて取り組めた。',0); service.close()
    before={p.name:p.read_bytes() for p in Path(folder).glob('*.json')}
    root=tk.Tk(); root.tk.call('tk','scaling',2.666667)
    app=TomerisWindow(root,data_dir=Path(folder),demo=True); wait(root,app)
    app.view('plan_history'); history=app.plan_history_panel; wait(root,app)
    history.weekly_button.invoke(); panel=app.weekly_panel; wait(root,app)
    text=panel.body.get('1.0','end')
    assert '落ち着いて取り組めた。' in text and '完了チェックあり：1件' in text
    panel.window.geometry('580x460'); root.update()
    for button in [panel.reload,panel.exit_button]:
        y=button.winfo_rooty()-panel.window.winfo_rooty()
        assert y>=0 and y+button.winfo_height()<=panel.window.winfo_height()
    panel.reload.invoke(); wait(root,app)
    panel.close(); assert history.window.grab_current()==history.window
    history.close(); app.close()
    limit=time.monotonic()+8
    while time.monotonic()<limit:
        try:
            root.update()
            if not root.winfo_exists(): break
        except tk.TclError: break
        time.sleep(.02)
    else: raise AssertionError('Close failed')
    assert before=={p.name:p.read_bytes() for p in Path(folder).glob('*.json')}
print('Weekly UI: open, counts, original reflection, reload, modal close, layout and unchanged records: OK')
