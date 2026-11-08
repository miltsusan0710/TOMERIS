from pathlib import Path
from unittest.mock import patch
from tkinter import ttk
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v041'))
from tomeris_tomorrow_ui import PlanHistoryPanel
from tomeris_plans import today

def descendants(w):
 for c in w.winfo_children():
  yield c
  yield from descendants(c)
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
 root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
 try:
  app.service.save_plan('持ち越し確認',10,[dict(title='明日へ引き継ぐ作業',minutes=10)],today())
  panel=PlanHistoryPanel(app);app.plan_history_panel=panel;wait(root,app)
  panel.tomorrow();wait(root,app);root.update()
  button=next(w for w in descendants(panel.window) if isinstance(w,ttk.Button) and w.cget('text')=='選んだ行動を保存')
  with patch('tomeris_tomorrow_ui.messagebox.askyesno',return_value=True):button.invoke()
  wait(root,app);root.update()
  assert len(app.service._plans())==2
  assert app.service._plans()[1]['date']>today()
  panel.close()
 finally:stop(root,app)
print('Tomorrow UI review, explicit save, and history preservation OK')


