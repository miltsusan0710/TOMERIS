import sys,tempfile,time,zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v016 import TomerisWindow

def wait(root,app):
    deadline=time.monotonic()+8
    while app.busy and time.monotonic()<deadline:
        root.update(); time.sleep(.02)
    assert not app.busy
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    root=tk.Tk(); root.withdraw(); app=TomerisWindow(root,data_dir=Path(folder)/'data',demo=True); wait(root,app)
    before=app.service.memory_path.read_bytes(); target=Path(folder)/'backup.zip'
    with patch('tomeris_desktop_v016.filedialog.asksaveasfilename',return_value=''):
        app.data_menu.invoke(0)
    assert not target.exists() and not app.busy
    with patch('tomeris_desktop_v016.filedialog.asksaveasfilename',return_value=str(target)):
        app.data_menu.invoke(0)
        assert app.data_menu.entrycget(0,'state')=='disabled'
        wait(root,app)
    with zipfile.ZipFile(target) as archive:
        assert archive.read('tomeris_memory.json')==before
    assert '内容の一致を確認しました' in app.transcript.get('1.0','end')
    backup_bytes=target.read_bytes()
    with patch('tomeris_desktop_v016.filedialog.asksaveasfilename',return_value=str(target)):
        app.data_menu.invoke(0); wait(root,app)
    assert target.read_bytes()==backup_bytes
    assert '別の名前で保存' in app.transcript.get('1.0','end')
    assert app.service.memory_path.read_bytes()==before
    app.close(); deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        try:
            root.update()
            if not root.winfo_exists(): break
        except tk.TclError: break
        time.sleep(.02)
    else: raise AssertionError('close failed')
print('Backup menu: cancel, save, busy state, content verification, overwrite refusal, unchanged memory: OK')
