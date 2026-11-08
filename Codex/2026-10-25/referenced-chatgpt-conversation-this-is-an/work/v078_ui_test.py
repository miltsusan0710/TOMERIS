import sys,tempfile
from pathlib import Path
base=Path(__file__).resolve().parents[1];sys.path.insert(0,str(base/'outputs'))
import tkinter as tk
from types import SimpleNamespace
from tomeris_adaptive_collection import DesktopService
from tomeris_collection_ui_v078 import CollectionPanel
root=tk.Tk();root.withdraw()
try:
 with tempfile.TemporaryDirectory(dir=base/'work'/'v07') as folder:
  service=DesktopService(Path(folder),demo=True)
  try:
   service.remember_attempts([dict(action='exact',success=False),dict(action='normalized',success=True)])
   def submit(kind,work,message):
    callback,outcome=work();callback(outcome)
   app=SimpleNamespace(root=root,busy=False,closing=False,service=service,submit=submit)
   panel=CollectionPanel(app);root.update_idletasks()
   text=panel.results.get('1.0','end')
   assert '取得経験：2件' in text
   assert '中点・全半角の表記違いを許容 → 対象名の完全一致' in text
   assert '会話モデルの訓練ではありません' in text
   print('PASS: actual Tk state shows learned order and limits')
  finally:service.close()
finally:root.destroy()
