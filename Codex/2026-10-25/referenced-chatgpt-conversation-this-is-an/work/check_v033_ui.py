from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v033'))
from test_desktop_research_continuation import ROWS,page
import tomeris_evidence_v029 as evidence
import tomeris_search_methods as providers
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
 root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
 try:
  app.service.demo=False
  with patch.object(providers,'wikipedia_search',return_value=ROWS),patch.object(evidence,'wikipedia_page',side_effect=page):
   app.entry.insert('1.0','アイアンマンについて調べて');app.send();wait(root,app)
   assert len(app.service.catalogue.rows)==2
  app.learning_action('学習した資料を見せて');wait(root,app);assert '2件' in app.last_answer
  app.learning_action('ネット学習を停止');wait(root,app);assert not app.service.catalogue.enabled
  app.learning_action('ネット学習を再開');wait(root,app);assert app.service.catalogue.enabled
  app.learning_action('学習した資料を消去');wait(root,app);assert not app.service.catalogue.rows
  with patch('tomeris_research_learning.fetch_latest',return_value='気象庁の発表：震源地未確認'):
   app.entry.delete('1.0','end');app.entry.insert('1.0','今の地震の震源は？');app.send();wait(root,app);assert '震源地未確認' in app.last_answer
 finally:stop(root,app)
print('Learning menu and current earthquake routing: OK')
