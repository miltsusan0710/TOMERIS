from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v037'))
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
 root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
 try:
  for text,expected in [('Googleで調べて','何を調べますか'),('計算: 2+2','結果：4'),('明後日の天気は？','市区町村'),('キャンセル','取り消しました'),('荒川区の明日の天気','荒川区の明日'),('明日の天気は？','市区町村'),('明後日は？','明後日の天気を調べる市区町村'),('平塚市','平塚市の明後日')]:
   app.entry.delete('1.0','end');app.entry.insert('1.0',text);app.send();wait(root,app);assert expected in app.last_answer,(text,app.last_answer)
 finally:stop(root,app)
print('Context UI: search prompt -> calculation, weather cancellation, fresh place clarification and day continuity OK')
