from pathlib import Path
helpers=Path('work/check_memory_edit_ui.py').read_text(encoding='utf-8-sig').split("with tempfile.TemporaryDirectory(dir='work/v07') as folder:")[0]
exec(helpers.replace('tomeris_desktop_v020','tomeris_desktop_v036'))
from test_desktop_earthquake_followup import get
import tomeris_earthquake_followup as quake
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
 root=tk.Tk();app=TomerisWindow(root,data_dir=Path(folder),demo=True);wait(root,app)
 try:
  app.service.demo=False;first=get(minute='08');second=get(first,minute='09',place='試験震源地');third=get(second,minute='10',kind='取消')
  with patch.object(quake,'snapshot',side_effect=[first,second,third]):
   for text,expected in [('今の地震の震源は？','未確認'),('その後は？','試験震源地'),('地震の続報は？','取消')]:
    app.entry.delete('1.0','end');app.entry.insert('1.0',text);app.send();wait(root,app);assert expected in app.last_answer
   assert '試験震源地' not in app.last_answer
  app.entry.insert('1.0','計算: 1+2');app.send();wait(root,app);assert app.service.earthquake_record is None
 finally:stop(root,app)
print('Earthquake UI: flash -> same-event update -> cancellation -> reset OK')
