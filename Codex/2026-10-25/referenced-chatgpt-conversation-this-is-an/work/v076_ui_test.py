import sys,tempfile
from pathlib import Path
base=Path(__file__).resolve().parents[1];sys.path.insert(0,str(base/'outputs'))
import tkinter as tk
from types import SimpleNamespace
from unittest.mock import patch
from tomeris_trial_coverage_ui import open_coverage
root=tk.Tk();root.withdraw()
try:
 with tempfile.TemporaryDirectory(dir=base/'work'/'v07') as directory:
  def submit(kind,work,message):
   callback,outcome=work();callback(outcome)
  app=SimpleNamespace(root=root,busy=False,closing=False,service=SimpleNamespace(data_dir=Path(directory)),submit=submit)
  def contents(widget):
   result=[]
   for child in widget.winfo_children():
    if isinstance(child,tk.Text):result.append(child.get('1.0','end'));assert str(child.cget('state'))=='disabled'
    result.extend(contents(child))
   return result
  open_coverage(app);root.update_idletasks()
  assert any('試行総数：0' in s for s in contents(root))
  assert not list(Path(directory).iterdir())
  folder=Path(directory)/'research_trials';folder.mkdir();(folder/'broken.json').write_text('{}')
  open_coverage(app);root.update_idletasks()
  assert any('不正・読み取り不能：1' in s and 'broken.json' in s for s in contents(root))
  with patch('tomeris_trial_coverage_ui.summarize',side_effect=OSError('試験エラー')):open_coverage(app)
  assert any('集計できませんでした：試験エラー' in s for s in contents(root))
  print('PASS: empty report, invalid record, read-only text, error display')
finally:root.destroy()
