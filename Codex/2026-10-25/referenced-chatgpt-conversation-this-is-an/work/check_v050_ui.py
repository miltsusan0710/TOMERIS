from pathlib import Path
from unittest.mock import patch
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v050'))
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
 root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
 try:
  app.open_collection();panel=app.collection_panel;wait(root,app)
  panel.topics.delete('1.0','end');panel.topics.insert('1.0','情報検索')
  with patch('tomeris_collection_ui.messagebox.askyesno',return_value=False):panel.save()
  assert len(app.service.collection_topics)==3
  with patch('tomeris_collection_ui.messagebox.askyesno',return_value=True):panel.save();wait(root,app)
  assert app.service.collection_topics==['情報検索'];assert not app.service.auto_sources_enabled
  with patch('tomeris_collection_ui.messagebox.askyesno',return_value=True):panel.toggle(True);wait(root,app)
  assert app.service.auto_sources_enabled
  panel.close()
 finally:stop(root,app)
print('Collection UI confirm/cancel, save-stops and explicit resume OK')
