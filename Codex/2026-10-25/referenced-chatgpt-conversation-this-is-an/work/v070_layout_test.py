import sys,time,tempfile
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v070 import TomerisWindow
tempfile.tempdir=str(Path('work/v07').resolve())
with tempfile.TemporaryDirectory() as d:
 r=tk.Tk();r.withdraw();app=TomerisWindow(r,Path(d),True)
 def pump():
  for _ in range(10):r.update();time.sleep(.03)
 r.deiconify();pump()
 app.append('あなた','画像を見てください。')
 app.append('トメリス','長い説明とリンクの表示確認です。'*80+'\nhttps://example.com/')
 for geometry in ('1280x850','880x760'):
  r.geometry(geometry);pump();app.change_text_size(2);pump()
  for row,body,box,title in app.transcript.cards:
   assert body.get('1.0','end-1c')
   assert box.winfo_height()>=body.winfo_reqheight(),(geometry,box.winfo_height(),body.winfo_reqheight())
   assert box.winfo_width()<=app.transcript.canvas.winfo_width()
  assert app.send_button.winfo_rooty()+app.send_button.winfo_height()<=r.winfo_rooty()+r.winfo_height()
 assert len(app.media_actions)==5
 assert app.transcript.cards[-1][1].tag_ranges('url0')
 app.closing=True;app.jobs.put(None)
 for _ in range(100):
  try:r.update()
  except tk.TclError:break
  time.sleep(.02)
 print('PASS: small/large window, text resize, long cards, links, composer, close')

