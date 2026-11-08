from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v035'))
from test_desktop_source_backup import ROW
import tomeris_sources_ui as ui
from tomeris_page_reader import PageError
import ctypes
ctypes.windll.user32.SetProcessDPIAware()
for scale in (1.333333,2.666667):
 with tempfile.TemporaryDirectory(dir='work/v07') as folder:
  root=tk.Tk();root.tk.call('tk','scaling',scale);app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
  try:
   app.service.catalogue.save([ROW,dict(ROW,title='別資料',url='https://example.com/2')],False)
   app.open_sources();wait(root,app);panel=app.sources_panel
   panel.window.geometry('640x580');root.update()
   bounds(panel.window,[panel.query,panel.search,panel.tree,panel.detail,panel.check,panel.delete,panel.exit])
   assert panel.detail.winfo_height()>40
   panel.query.insert(0,'テスト');panel.reload();wait(root,app);assert len(panel.rows)==1
   panel.tree.selection_set('0');root.update();assert '未検証' in panel.detail.get('1.0','end') and '2026-10-29' in panel.detail.get('1.0','end')
   app.service.demo=False;before=app.service.catalogue.path.read_bytes()
   with patch('tomeris_source_management.fetch_page',return_value=dict(url=ROW['url'],text='新しい本文')):
    panel.check_selected();wait(root,app);assert '再取得成功' in panel.detail.get('1.0','end')
   with patch('tomeris_source_management.fetch_page',side_effect=PageError('取得不可')):
    panel.check_selected();wait(root,app);assert '再取得失敗' in panel.detail.get('1.0','end')
   bounds(panel.window,[panel.check,panel.delete,panel.exit]);assert panel.detail.winfo_height()>40
   assert before==app.service.catalogue.path.read_bytes()
   with patch.object(ui.messagebox,'askyesno',return_value=False):panel.delete_selected()
   assert len(app.service.catalogue.rows)==2
   with patch.object(ui.messagebox,'askyesno',return_value=True):panel.delete_selected();wait(root,app)
   assert len(app.service.catalogue.rows)==1 and not panel.rows
   panel.close();app.entry.insert('1.0','計算: 1+2');app.send();wait(root,app);assert '結果：3' in app.last_answer
  finally:stop(root,app)
print('Source management UI: two DPI layouts, search, retrieval states, cancel/delete, chat return OK')
