import sys,time,tempfile
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v083 import TomerisWindow
tempfile.tempdir=str(Path('work/v07').resolve())
with tempfile.TemporaryDirectory() as d:
 r=tk.Tk();app=TomerisWindow(r,Path(d),True)
 def pump():
  for _ in range(10):r.update();time.sleep(.03)
 try:
  pump()
  app.append('あなた','表示の確認です。')
  app.append('トメリス','最初の文です。\n'+('長い説明の表示確認です。\n'*150)+'https://example.com/')
  for geometry in ('1280x850','880x760'):
   r.geometry(geometry);pump();app.change_text_size(1);pump()
   app.transcript.see('end');pump()
   assert app.transcript.body.dlineinfo(app.transcript.latest+'+1line')
   assert app.send_button.winfo_rooty()+app.send_button.winfo_height()<=r.winfo_rooty()+r.winfo_height()
  assert {'image','listen','speak','batch','stop'} <= set(app.media_actions)
  assert app.last_answer.startswith('最初の文です。')
  print('PASS: desktop integration, both sizes, composer, copy source, media actions')
 finally:
  app.close()
  for _ in range(100):
   try:r.update()
   except tk.TclError:break
   time.sleep(.02)
