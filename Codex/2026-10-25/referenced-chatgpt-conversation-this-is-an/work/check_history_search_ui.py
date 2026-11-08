import sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v018 import TomerisWindow
from tomeris_history_search import DesktopService

def wait(root,app):
    deadline=time.monotonic()+8
    while app.busy and time.monotonic()<deadline:
        root.update(); time.sleep(.02)
    assert not app.busy
with tempfile.TemporaryDirectory(dir='work/v07') as directory:
    service=DesktopService(directory,demo=True)
    service.store.data['conversations']=[{'user':f'質問{i}','tomeris':'回答'} for i in range(55)]
    service.store.data['conversations'][0]={'user':'プログラムについて','tomeris':'ＰＹＴＨＯＮで試せます。'}
    service.store.save(); before=service.memory_path.read_bytes(); service.close()
    root=tk.Tk(); root.tk.call('tk','scaling',2.666667)
    app=TomerisWindow(root,data_dir=Path(directory),demo=True); wait(root,app)
    app.view('history'); panel=app.conversation_panel; wait(root,app)
    assert panel.list.size()==50 and panel.result['total']==55
    panel.next.invoke(); wait(root,app); assert panel.list.size()==5 and panel.result['offset']==50
    panel.previous.invoke(); wait(root,app); assert panel.result['offset']==0
    panel.query.set('python'); panel.search_button.invoke(); wait(root,app)
    assert panel.list.size()==1 and 'ＰＹＴＨＯＮ' in panel.detail.get('1.0','end')
    panel.query.set('存在しない言葉'); panel.search_button.invoke(); wait(root,app)
    assert panel.list.size()==0 and '一致する会話はありません' in panel.detail.get('1.0','end')
    panel.clear_button.invoke(); wait(root,app); assert panel.result['total']==55
    panel.window.geometry('640x580'); root.update()
    for widget in [panel.entry,panel.search_button,panel.clear_button,panel.previous,panel.next,panel.exit_button]:
        x=widget.winfo_rootx()-panel.window.winfo_rootx(); y=widget.winfo_rooty()-panel.window.winfo_rooty()
        assert x>=0 and y>=0 and x+widget.winfo_width()<=panel.window.winfo_width() and y+widget.winfo_height()<=panel.window.winfo_height()
    assert panel.detail.winfo_height()>1
    panel.close(); app.close(); deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        try:
            root.update()
            if not root.winfo_exists(): break
        except tk.TclError: break
        time.sleep(.02)
    else: raise AssertionError('close failed')
    assert (Path(directory)/'tomeris_memory.json').read_bytes()==before
print('Conversation search UI: search, full answer, no results, clear, pagination, unchanged memory, 200% layout: OK')
