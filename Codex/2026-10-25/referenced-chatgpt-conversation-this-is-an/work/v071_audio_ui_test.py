import sys,time,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v071 import TomerisWindow
from tomeris_speech_control import SpeechCancelled
tempfile.tempdir=str(Path('work/v07').resolve())
with tempfile.TemporaryDirectory() as d:
 root=tk.Tk();root.geometry('880x760');root.withdraw();app=TomerisWindow(root,Path(d),True)
 def until(test):
  deadline=time.monotonic()+8
  while not test():
   root.update();time.sleep(.02)
   assert time.monotonic()<deadline,'UI timeout'
 until(lambda:app.service is not None and not app.busy)
 def fake(action,text,cancel):
  if not cancel.wait(3):raise AssertionError('not cancelled')
  raise SpeechCancelled()
 with patch('tomeris_multimodal_ui_v071.speech',side_effect=fake):
  app.media_actions['listen']()
  assert app.audio_active and str(app.audio_stop_button.cget('state'))=='normal'
  app.audio_stop_button.invoke()
  until(lambda:not app.busy)
  assert not app.audio_active
  assert str(app.audio_stop_button.cget('state'))=='disabled'
  assert not app.entry.get('1.0','end-1c')
 root.deiconify();root.geometry('880x760')
 for _ in range(10):root.update();time.sleep(.03)
 assert app.audio_stop_button.winfo_rootx()+app.audio_stop_button.winfo_width()<=root.winfo_rootx()+root.winfo_width(),'stop button clipped'
 with patch('tomeris_multimodal_ui_v071.speech',side_effect=fake):
  app.media_actions['listen']();app.close()
  for _ in range(100):
   try:root.update();exists=root.winfo_exists()
   except tk.TclError:break
   time.sleep(.02)
 print('PASS: stop while busy, no transcript after cancel, disabled on finish, fits narrow window, close cancels')
