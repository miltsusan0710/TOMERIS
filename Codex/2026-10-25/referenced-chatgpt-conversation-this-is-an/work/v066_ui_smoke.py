import sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
from tomeris_desktop_v066 import TomerisWindow
import tkinter as tk
tempfile.tempdir=str(Path('work/v07').resolve())
with tempfile.TemporaryDirectory() as d:
 root=tk.Tk();root.withdraw();app=TomerisWindow(root,Path(d),True)
 limit=time.monotonic()+10
 while app.service is None and time.monotonic()<limit:root.update();time.sleep(.05)
 assert app.service is not None
 menu=root.nametowidget(root.cget('menu'))
 labels=[menu.entrycget(i,'label') for i in range(1,menu.index('end')+1)]
 assert '画像・音声・依頼' in labels
 app.closing=True;app.jobs.put(None)
 while time.monotonic()<limit:
  try:root.update()
  except tk.TclError:break
  try:
   if not root.winfo_exists():break
  except tk.TclError:break
  time.sleep(.05)
 print('UI startup, menu, orderly close: OK')
