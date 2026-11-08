import sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v014 import TomerisWindow
from tomeris_plan_reflection import DesktopService
from tomeris_plans import today

def wait(root,app):
    limit=time.monotonic()+8
    while app.busy and time.monotonic()<limit:
        root.update(); time.sleep(.02)
    assert not app.busy

with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    service=DesktopService(folder,demo=True)
    service.save_plan('振り返り確認',10,[{'title':'一歩進める','minutes':5}],today())
    old={p.name:p.read_bytes() for p in Path(folder).glob('*.json')}; service.close()
    root=tk.Tk(); root.withdraw(); app=TomerisWindow(root,data_dir=Path(folder),demo=True); wait(root,app)
    app.view('plan_history'); history=app.plan_history_panel; history.window.withdraw(); wait(root,app)
    history.reflect_button.invoke(); editor=app.reflection_panel; editor.window.withdraw(); wait(root,app)
    editor.body.insert('1.0','小さく始められた。次も5分から。')
    with patch('tomeris_reflection_ui.messagebox.askyesno',return_value=False):
        editor.close(); assert editor.window.winfo_exists()
    assert not (Path(folder)/'plan_reflections.json').exists()
    with patch.object(app.service,'save_reflection',side_effect=OSError('test')):
        editor.save_button.invoke(); wait(root,app)
        assert '小さく始められた' in editor.body.get('1.0','end')
        assert '失敗' in editor.notice.get()
    editor.save_button.invoke(); wait(root,app)
    assert '保存しました' in editor.notice.get()
    editor.close()
    assert '小さく始められた' in history.detail.get('1.0','end')
    assert history.window.grab_current()==history.window
    history.reflect_button.invoke(); editor=app.reflection_panel; editor.window.withdraw(); wait(root,app)
    assert '小さく始められた' in editor.body.get('1.0','end')
    editor.close(); history.close(); app.close()
    limit=time.monotonic()+8
    while time.monotonic()<limit:
        try:
            root.update()
            if not root.winfo_exists(): break
        except tk.TclError: break
        time.sleep(.02)
    else: raise AssertionError('Close failed')
    for name,data in old.items(): assert (Path(folder)/name).read_bytes()==data
print('Reflection UI: load, unsaved close, failed save, explicit save, reopen, history and unchanged plan/memory: OK')
