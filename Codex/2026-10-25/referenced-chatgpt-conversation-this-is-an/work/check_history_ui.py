import sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v012 import TomerisWindow
from tomeris_plan_history import DesktopService
from tomeris_plans import today

def wait(root,app):
    deadline=time.monotonic()+8
    while app.busy and time.monotonic()<deadline:
        root.update(); time.sleep(.02)
    assert not app.busy

with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    service=DesktopService(folder,demo=True)
    with patch('tomeris_plans.today',return_value='2026-10-25'):
        service.save_plan('以前の計画',10,[{'title':'以前の作業','minutes':5}],'2026-10-25')
    service.save_plan('今日の計画',10,[{'title':'今日の作業','minutes':5}],today())
    state=service.today_plan(); service.set_completion(state['id'],0,True)
    service.close()
    names=['daily_plans.json','plan_progress.json','tomeris_memory.json']
    before={name:(Path(folder)/name).read_bytes() for name in names}
    root=tk.Tk(); root.withdraw(); app=TomerisWindow(root,data_dir=Path(folder),demo=True); wait(root,app)
    app.view('plan_history'); panel=app.plan_history_panel; panel.window.withdraw(); wait(root,app)
    assert panel.list.size()==2
    assert '［完了］' in panel.detail.get('1.0','end')
    panel.date_box.set('2026-10-25'); panel.filter()
    assert panel.list.size()==1 and '以前の作業' in panel.detail.get('1.0','end')
    assert 'チェック記録なし' in panel.detail.get('1.0','end')
    panel.load(); wait(root,app)
    assert panel.date_box.get()=='2026-10-25'
    panel.close()
    app.view('today'); app.today_panel.window.withdraw(); wait(root,app)
    assert app.today_panel.variables[0].get() is True
    app.today_panel.close(); app.close()
    deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        try:
            root.update()
            if not root.winfo_exists():
                break
        except tk.TclError:
            break
        time.sleep(.02)
    else:
        raise AssertionError('Close failed')
    assert before=={name:(Path(folder)/name).read_bytes() for name in names}
print('History UI, date filter, reload, completion compatibility and unchanged files: OK')
