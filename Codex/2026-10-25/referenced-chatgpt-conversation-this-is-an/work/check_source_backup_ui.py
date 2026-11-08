import sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v034 import TomerisWindow
from tomeris_desktop_v034 import DesktopService
from tomeris_plans import today

def wait(root,app):
    limit=time.monotonic()+8
    while app.busy and time.monotonic()<limit:
        root.update(); time.sleep(.02)
    assert not app.busy
with tempfile.TemporaryDirectory(dir='work/v07') as directory:
    parent=Path(directory)
    service=DesktopService(parent/'data',demo=True)
    service.save_plan('復元操作を確認',10,[{'title':'確認する','minutes':5}],today())
    service.catalogue.save([dict(url='https://example.com/article',title='テスト資料',excerpt='未検証の引用',retrieved='2026-10-29T01:00:00+09:00')],False)
    archive=parent/'backup.zip'; service.export_backup(archive); service.close()
    before={p.name:p.read_bytes() for p in (parent/'data').glob('*.json')}
    root=tk.Tk(); root.tk.call('tk','scaling',2.666667)
    app=TomerisWindow(root,data_dir=parent/'data',demo=True); wait(root,app)
    with patch('tomeris_desktop_v034.filedialog.askopenfilename',return_value=''):
        app.data_menu.invoke(1)
    assert not hasattr(app,'restore_panel')
    with patch('tomeris_desktop_v034.filedialog.askopenfilename',return_value=str(archive)):
        app.data_menu.invoke(1)
    panel=app.restore_panel; wait(root,app)
    assert panel.checked and '検査が完了' in panel.body.get('1.0','end')
    assert '保存資料 1件 / 資料学習：停止' in panel.body.get('1.0','end')
    panel.window.geometry('600x500'); root.update()
    for button in [panel.restore_button,panel.open_button,panel.exit_button]:
        x=button.winfo_rootx()-panel.window.winfo_rootx(); y=button.winfo_rooty()-panel.window.winfo_rooty()
        assert x>=0 and y>=0 and x+button.winfo_width()<=panel.window.winfo_width() and y+button.winfo_height()<=panel.window.winfo_height()
    with patch('tomeris_restore_ui_v034.filedialog.askdirectory',return_value=''):
        panel.restore_button.invoke()
    assert not list(parent.glob('tomeris_restored_*'))
    with patch('tomeris_restore_ui_v034.filedialog.askdirectory',return_value=str(parent)):
        panel.restore_button.invoke(); wait(root,app)
    restored=Path(panel.restored)
    assert before=={p.name:p.read_bytes() for p in restored.iterdir()}
    with patch('tomeris_restore_ui_v034.subprocess.Popen') as launch:
        panel.open_button.invoke()
        args=launch.call_args.args[0]
        assert args[-2:]==['--data-dir',str(restored)]
    panel.close(); app.close()
    limit=time.monotonic()+8
    while time.monotonic()<limit:
        try:
            root.update()
            if not root.winfo_exists(): break
        except tk.TclError: break
        time.sleep(.02)
    else: raise AssertionError('Close failed')
    assert before=={p.name:p.read_bytes() for p in (parent/'data').glob('*.json')}
print('Restore UI: preview, cancel, new folder, exact data, isolated launch arguments, original preserved, 200% layout: OK')
