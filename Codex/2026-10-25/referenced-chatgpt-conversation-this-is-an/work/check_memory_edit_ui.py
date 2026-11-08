import sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v020 import TomerisWindow

def wait(root,app):
    deadline=time.monotonic()+8
    while app.busy and time.monotonic()<deadline:
        root.update(); time.sleep(.02)
    root.update(); assert not app.busy

def bounds(window,widgets):
    window.update()
    for w in widgets:
        x=w.winfo_rootx()-window.winfo_rootx(); y=w.winfo_rooty()-window.winfo_rooty()
        assert x>=0 and y>=0 and x+w.winfo_width()<=window.winfo_width() and y+w.winfo_height()<=window.winfo_height(), (w,x,y,window.winfo_geometry())

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
    root=tk.Tk(); root.tk.call('tk','scaling',2.666667)
    app=TomerisWindow(root,data_dir=Path(folder),demo=True); wait(root,app)
    app.service.remember('Pythonを学ぶ','目標'); before=app.service.memory_path.read_bytes()
    app.view('memories'); wait(root,app); panel=app.memory_panel
    panel.window.geometry('640x580'); root.update()
    bounds(panel.window,[panel.entry,panel.edit_button,panel.previous,panel.next,panel.exit_button]); assert panel.detail.winfo_height()>1
    panel.edit(); editor=panel.editor; editor.window.geometry('600x500'); root.update()
    bounds(editor.window,[editor.body,editor.save_button,editor.cancel_button]); assert editor.body.winfo_height()>1
    editor.body.delete('1.0','end'); editor.body.insert('1.0','Pythonを毎日練習する')
    with patch('tomeris_memory_edit_ui.messagebox.askyesno',return_value=False): editor.close()
    assert editor.window.winfo_exists()
    assert app.service.memory_path.read_bytes()==before
    with patch.object(app.service.store,'save',side_effect=OSError('保存失敗テスト')):
        editor.save(); wait(root,app)
    assert editor.window.winfo_exists() and '保存失敗' in editor.message.get()
    assert editor.body.get('1.0','end-1c')=='Pythonを毎日練習する'
    assert app.service.memory_path.read_bytes()==before
    editor.save(); wait(root,app)
    assert not editor.window.winfo_exists()
    text=panel.detail.get('1.0','end'); assert 'Pythonを毎日練習する' in text and '変更前' in text and 'Pythonを学ぶ' in text
    panel.query.set('notfound'); panel.search(); wait(root,app); assert panel.result['total']==0
    assert str(panel.edit_button['state'])=='disabled'
    panel.clear(); wait(root,app); panel.edit(); editor=panel.editor
    editor.body.insert('end','キャンセル')
    with patch('tomeris_memory_edit_ui.messagebox.askyesno',return_value=True): editor.close()
    panel.close(); stop(root,app)
    root=tk.Tk(); root.withdraw(); app=TomerisWindow(root,data_dir=Path(folder),demo=True); wait(root,app)
    app.view('memories'); wait(root,app)
    assert app.memory_panel.result['rows'][0]['text']=='Pythonを毎日練習する'
    assert len(app.memory_panel.result['rows'][0]['edit_history'])==1
    app.memory_panel.close(); stop(root,app)
print('Memory UI: search, edit, failed save, retry, history, cancel, restart, 200% layout: OK')
