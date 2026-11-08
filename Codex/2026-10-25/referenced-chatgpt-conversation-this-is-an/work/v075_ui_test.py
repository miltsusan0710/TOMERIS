import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'outputs'))
import tkinter as tk
from unittest.mock import patch
from types import SimpleNamespace
from tomeris_experiment_view import open_experiment
root=tk.Tk();root.withdraw()
try:
 with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent/'v07') as directory:
  jobs=[]
  def submit(kind,work,message):
   jobs.append(kind);callback,outcome=work();callback(outcome)
  app=SimpleNamespace(root=root,busy=False,closing=False,service=SimpleNamespace(data_dir=Path(directory)),submit=submit)
  with patch('tkinter.filedialog.askopenfilename',return_value=''):open_experiment(app)
  assert not jobs
  path=Path(__file__).resolve().parents[1]/'outputs'/'bandit_synthetic_examples.json'
  with patch('tkinter.filedialog.askopenfilename',return_value=str(path)):open_experiment(app)
  root.update_idletasks()
  windows=[w for w in root.winfo_children() if isinstance(w,tk.Toplevel)]
  assert len(windows)==1
  def descendants(widget):
   for child in widget.winfo_children():
    yield child
    yield from descendants(child)
  contents=[w.get('1.0','end') for w in descendants(windows[0]) if isinstance(w,tk.Text)]
  assert any('人工データによる動作実験' in text and '通常の検索方法' in text for text in contents)
  assert not list(Path(directory).iterdir())
  print('PASS: chooser cancel, explicit offline experiment, result text, no data writes')
finally:root.destroy()
