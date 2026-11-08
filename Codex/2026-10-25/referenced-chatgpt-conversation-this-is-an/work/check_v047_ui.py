from pathlib import Path
from unittest.mock import patch
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v047'))
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
 root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
 try:
  app.service.demo=False;app.service.auto_sources_next=0
  page=dict(title='論理的思考',url='https://ja.wikipedia.org/wiki/test',text='論理的思考は考え方を整理して理解するために説明されている概念です。')
  with patch('tomeris_public_learning.wikipedia_search',return_value=[dict(title='論理的思考')]),patch('tomeris_public_learning.wikipedia_page',return_value=page):
   app.auto_source_tick();wait(root,app)
  assert len(app.service.catalogue.rows)==1
  app.auto_source_action('自動資料収集を停止');wait(root,app);assert not app.service.auto_sources_enabled
 finally:stop(root,app)
print('Idle collection worker and stop menu OK (temporary data, mocked network)')
