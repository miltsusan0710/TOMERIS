import sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v011 import TomerisWindow
from tomeris_plan_progress import DesktopService,today

def wait_ready(root,app):
    deadline=time.monotonic()+8
    while app.busy and time.monotonic()<deadline:
        root.update(); time.sleep(.02)
    assert not app.busy

def shutdown(root,app):
    app.close()
    deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        try:
            root.update()
            if not root.winfo_exists():
                return
        except tk.TclError:
            return
        time.sleep(.02)
    raise AssertionError('Close timed out')

with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    service=DesktopService(folder,demo=True)
    service.save_plan('動作確認',10,[{'title':'チェックする','minutes':5}],today())
    memory=service.memory_path.read_bytes(); plan=(Path(folder)/'daily_plans.json').read_bytes()
    service.close()
    root=tk.Tk(); root.withdraw(); app=TomerisWindow(root,data_dir=Path(folder),demo=True)
    wait_ready(root,app)
    app.view('today'); panel=app.today_panel; panel.window.withdraw(); wait_ready(root,app)
    assert panel.variables[0].get() is False
    panel.checks[0].invoke(); wait_ready(root,app)
    assert panel.variables[0].get() is True and '完了 1 / 1' in panel.summary.get()
    with patch.object(app.service,'set_completion',side_effect=OSError('test failure')):
        panel.checks[0].invoke(); wait_ready(root,app)
        assert panel.variables[0].get() is True and '失敗' in panel.notice.get()
    panel.close(); shutdown(root,app)
    root=tk.Tk(); root.withdraw(); app=TomerisWindow(root,data_dir=Path(folder),demo=True)
    wait_ready(root,app)
    app.view('today'); panel=app.today_panel; panel.window.withdraw(); wait_ready(root,app)
    assert panel.variables[0].get() is True
    panel.checks[0].invoke(); wait_ready(root,app)
    assert panel.variables[0].get() is False
    panel.close(); shutdown(root,app)
    assert (Path(folder)/'daily_plans.json').read_bytes()==plan
    assert (Path(folder)/'tomeris_memory.json').read_bytes()==memory
print('UI completion, failure rollback, restart, undo and original data preservation: OK')
