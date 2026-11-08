import sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v013 import TomerisWindow
from tomeris_plan_carry import DesktopService,today

def wait(root,app):
    deadline=time.monotonic()+8
    while app.busy and time.monotonic()<deadline:
        root.update(); time.sleep(.02)
    assert not app.busy

with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    service=DesktopService(folder,demo=True)
    service.save_plan('確認',20,[{'title':'終わった行動','minutes':5},{'title':'残った行動','minutes':10}],today())
    original=service.today_plan(); service.set_completion(original['id'],0,True)
    before={p.name:p.read_bytes() for p in Path(folder).glob('*.json')}; service.close()
    root=tk.Tk(); root.withdraw(); app=TomerisWindow(root,data_dir=Path(folder),demo=True); wait(root,app)
    def open_draft():
        app.view('plan_history'); panel=app.plan_history_panel; panel.window.withdraw(); wait(root,app)
        panel.carry_button.invoke(); wait(root,app)
        app.plan_window.withdraw()
        assert app.plan_controls[4].get()=='残った行動'
        assert app.plan_controls[6].get()==''
        assert '未保存' in app.plan_window.title()
    open_draft()
    assert before=={p.name:p.read_bytes() for p in Path(folder).glob('*.json')}
    app.plan_window.destroy()
    assert before=={p.name:p.read_bytes() for p in Path(folder).glob('*.json')}
    open_draft()
    field=app.plan_controls[4]; field.delete(0,'end'); field.insert(0,'修正した行動')
    app.plan_controls[3].invoke(); wait(root,app)
    assert not app.plan_window.winfo_exists()
    state=app.service.today_plan()
    assert state['plan']['tasks']==[{'title':'修正した行動','minutes':10}]
    assert state['done']==[False]
    assert (Path(folder)/'plan_progress.json').read_bytes()==before['plan_progress.json']
    assert (Path(folder)/'tomeris_memory.json').read_bytes()==before['tomeris_memory.json']
    old=next(row for row in app.service.plan_history() if row['id']==original['id'])
    assert old['done']==[True,False]
    app.close(); deadline=time.monotonic()+8
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
print('Carry UI preview, cancel, edit, explicit save, reset checks, preserved original: OK')
