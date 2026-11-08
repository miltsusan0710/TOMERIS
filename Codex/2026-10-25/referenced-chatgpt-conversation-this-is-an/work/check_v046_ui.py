from pathlib import Path
from unittest.mock import patch
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v046'))
from tomeris_research_history_ui import ResearchHistoryPanel
GOOD='Ollamaはローカル環境でモデルを実行するためのツールとして説明されています。'
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
 root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
 try:
  for q in ('別の質問','Ollamaについて調べて'):
   app.service.research_journal.append(q,'選択設定：自動（実際の提供元は出典を参照）',[dict(title='過去の資料',url='https://example.com/old')])
  app.open_research_history();panel=app.research_history_panel;wait(root,app)
  assert len(panel.visible)==2
  panel.query.set('Ollama');root.update();assert len(panel.visible)==1
  assert '今回は再取得していません' in panel.detail.get('1.0','end')
  with patch('tomeris_research_history_ui.messagebox.askyesno',return_value=False),patch.object(app.service.methods,'candidates',side_effect=AssertionError('cancel must not search')):
   panel.retry_selected();wait(root,app)
  app.service.demo=False;row=dict(title='新規資料',url='https://example.com/new',snippet=GOOD)
  with patch('tomeris_research_history_ui.messagebox.askyesno',return_value=True),patch.object(app.service.methods,'candidates',return_value=([row],[])),patch('tomeris_evidence_v029.fetch_page',return_value=dict(row,text=GOOD,published='')) as fetch:
   panel.retry_selected();wait(root,app);fetch.assert_called_once()
  assert len(app.service.research_journal.read())==3
  with patch('tomeris_research_history_ui.messagebox.askyesno',return_value=True):
   panel.delete_selected();wait(root,app)
  assert len(app.service.research_journal.read())==2
  panel.close()
 finally:stop(root,app)
print('History UI: filtering, past label, cancel without network, confirmed re-fetch and single deletion OK')
