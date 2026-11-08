import sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v013 import TomerisWindow
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    root=tk.Tk(); root.withdraw()
    app=TomerisWindow(root,data_dir=Path(folder),demo=True)
    def wait_ready():
        deadline=time.monotonic()+8
        while app.busy and time.monotonic()<deadline:
            root.update(); time.sleep(.02)
        assert not app.busy,'UI worker did not finish'
    wait_ready()
    before=app.service.memory_path.read_bytes()
    app.service.demo=False
    app.open_google(); panel=app.google_panel; panel.window.withdraw()
    wait_ready()
    assert '初回設定' in panel.message.get()
    panel.fetch(); wait_ready()
    assert '未登録' in panel.output.get('1.0','end')
    assert app.service.memory_path.read_bytes()==before
    assert not app.service.google.vault.path.exists()
    panel.close()
    app.close()
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
        raise AssertionError('Window did not close')
print('GUI worker, initial setup, empty account display, unchanged memory, close: OK')
