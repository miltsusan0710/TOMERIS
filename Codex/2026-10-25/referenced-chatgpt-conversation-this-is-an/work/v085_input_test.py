import sys,tempfile,time,base64
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path('outputs').resolve()))
import tkinter as tk
from tomeris_desktop_v085 import TomerisWindow
from tomeris_composer_v085 import answer_image_bytes
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5XcAAAAASUVORK5CYII=')
tempfile.tempdir=str(Path('work/v07').resolve())
with tempfile.TemporaryDirectory() as folder:
 root=tk.Tk();app=TomerisWindow(root,Path(folder),True)
 sample=tk.PhotoImage(master=root,width=8,height=8);sample.put('#ff0000',to=(0,0,8,8))
 sample.write(str(Path(folder)/'sample.png'),format='png');PNG=(Path(folder)/'sample.png').read_bytes()
 try:
  for _ in range(30):root.update();time.sleep(.03)
  app.busy=False;app.control_state();app.entry.focus_force();root.update()
  app.entry.insert('1.0','最初')
  with patch('tomeris_composer_v085.ime_composing',return_value=False):
   app.entry.event_generate('<Control-Return>');root.update()
   assert app.entry.get('1.0','end-1c')=='最初\n'
   with patch.object(app,'send',return_value='break') as send:
    app.entry.event_generate('<Return>');root.update();send.assert_called_once()
  with patch('tomeris_composer_v085.ime_composing',return_value=True),patch.object(app,'send') as send:
   app.composer.enter();send.assert_not_called()
  with patch('tomeris_composer_v085.clipboard_image',return_value=None):
   assert app.composer.paste() is None
  with patch('tomeris_composer_v085.clipboard_image',return_value=PNG),patch.object(app,'submit') as submit:
   assert app.composer.paste()=='break';root.update()
   assert app.composer.data==PNG;assert app.composer.bar.winfo_ismapped();submit.assert_not_called()
   root.geometry('880x760');root.update()
   assert app.send_button.winfo_rooty()+app.send_button.winfo_height() <= root.winfo_rooty()+root.winfo_height()
  with patch.object(app,'submit',return_value=False):
   app.composer.send_image();assert app.composer.data==PNG
  with patch.object(app,'submit',return_value=True) as submit:
   app.composer.send_image();assert app.composer.data is None
   assert '送信していません' in submit.call_args.args[1]()
  with patch('tomeris_composer_v085.image_answer',side_effect=lambda path,q,m: str(path)):
   path=answer_image_bytes(PNG,'説明','test');assert not Path(path).exists()
  print('PASS: Enter/Ctrl+Enter, IME guard, text fallback, image preview, no auto-send, rejected-submit retention, temp cleanup')
 finally:
  app.close()
  for _ in range(100):
   try:root.update()
   except tk.TclError:break
   time.sleep(.02)
