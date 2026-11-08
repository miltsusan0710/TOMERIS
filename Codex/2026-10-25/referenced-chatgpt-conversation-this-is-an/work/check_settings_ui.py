import sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v019 import TomerisWindow

def wait(root,app):
    deadline=time.monotonic()+8
    while app.busy and time.monotonic()<deadline:
        root.update(); time.sleep(.02)
    assert not app.busy

def stop(root,app):
    app.close(); deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        try:
            root.update()
            if not root.winfo_exists(): return
        except tk.TclError: return
        time.sleep(.02)
    raise AssertionError('close failed')

with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    root=tk.Tk(); root.withdraw(); app=TomerisWindow(root,data_dir=Path(folder),demo=True); wait(root,app)
    memory=app.service.memory_path.read_bytes()
    app.model.set('qwen2.5:1.5b'); app.data_menu.invoke(2); wait(root,app)
    assert '起動時の会話モデル' in app.transcript.get('1.0','end')
    stop(root,app)
    root=tk.Tk(); root.withdraw(); app=TomerisWindow(root,data_dir=Path(folder),demo=True); wait(root,app)
    assert app.model.get()=='qwen2.5:1.5b'
    assert app.second_model.get()=='qwen2.5:3b'
    assert app.mode.get()=='会話' and app.use_memory.get() is False
    app.model.set('qwen2.5:3b'); app.refresh(); wait(root,app)
    assert app.model.get()=='qwen2.5:3b'
    stop(root,app)
    root=tk.Tk(); root.withdraw(); app=TomerisWindow(root,data_dir=Path(folder),demo=True); wait(root,app)
    assert app.model.get()=='qwen2.5:1.5b'
    stop(root,app)
    assert (Path(folder)/'tomeris_memory.json').read_bytes()==memory
print('Settings UI: explicit save, restart, comparison fallback, temporary selection, unchanged memory: OK')
