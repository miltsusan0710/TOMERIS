from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v039'))
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
 root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
 try:
  app.entry.insert('1.0','今日の予定は？');app.send();wait(root,app)
  assert '今日の計画はまだありません' in app.last_answer,app.last_answer
 finally:stop(root,app)
print('Schedule GUI: saved-plan lookup instead of generated schedule OK')
