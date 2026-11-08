"""Explicit clipboard image paste and keyboard composition; no clipboard polling."""
import base64
import ctypes
import json
import os
from pathlib import Path
import subprocess
import tempfile
import tkinter as tk
from tomeris_multimodal import image_answer

CLIPBOARD_SCRIPT = r'''
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$image=[System.Windows.Forms.Clipboard]::GetImage()
if ($null -eq $image) { [Console]::Write('{}'); exit }
try {
 if ([long]$image.Width*$image.Height -gt 20000000) { throw 'Image too large' }
 $stream=New-Object System.IO.MemoryStream
 try {
  $image.Save($stream,[System.Drawing.Imaging.ImageFormat]::Png)
  if ($stream.Length -gt 10485760) { throw 'Image too large' }
  [Console]::Write((@{png=[Convert]::ToBase64String($stream.ToArray());width=$image.Width;height=$image.Height}|ConvertTo-Json -Compress))
 } finally { $stream.Dispose() }
} finally { $image.Dispose() }
'''

def clipboard_image():
    if os.name != 'nt':return None
    user32=ctypes.windll.user32
    if not any(user32.IsClipboardFormatAvailable(f) for f in (2,8,17)):
        return None  # Leave ordinary text paste to Tk.
    result=subprocess.run(['powershell.exe','-NoProfile','-STA','-Command',CLIPBOARD_SCRIPT],
        capture_output=True, timeout=12, creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode or len(result.stdout)>15000000:
        raise ValueError('画像を貼り付けられませんでした。20メガピクセル・10MB以内の画像をコピーし直してください。')
    value=json.loads(result.stdout)
    if not value.get('png'):return None
    data=base64.b64decode(value['png'],validate=True)
    if len(data)>10*1024*1024 or not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('貼り付け画像の形式・サイズを確認できませんでした。')
    return data

def ime_composing(widget):
    if os.name != 'nt':return False
    imm=ctypes.windll.imm32
    imm.ImmGetContext.argtypes=[ctypes.c_void_p];imm.ImmGetContext.restype=ctypes.c_void_p
    imm.ImmGetCompositionStringW.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint]
    imm.ImmReleaseContext.argtypes=[ctypes.c_void_p,ctypes.c_void_p]
    hwnd=widget.winfo_id();context=imm.ImmGetContext(hwnd)
    if not context:return False
    try:return imm.ImmGetCompositionStringW(context,8,None,0)>0
    finally:imm.ImmReleaseContext(hwnd,context)

def answer_image_bytes(data,question,model):
    # Existing image validation / vision capability checks remain authoritative.
    with tempfile.TemporaryDirectory(prefix='tomeris-image-') as folder:
        path=Path(folder)/'clipboard.png';path.write_bytes(data)
        return image_answer(path,question,model)

class Composer:
    def __init__(self,app,parent):
        self.app=app;self.data=None;self.preview=None
        self.bar=tk.Frame(parent,bg='#102536')
        self.picture=tk.Label(self.bar,bg='#102536');self.picture.pack(side='left',padx=8,pady=4)
        self.label=tk.Label(self.bar,text='画像を添付しました（送信前）',bg='#102536',fg='#dceff6')
        self.label.pack(side='left')
        tk.Button(self.bar,text='画像を外す',command=self.clear).pack(side='right',padx=8)
        app.entry.bind('<<Paste>>',self.paste)
        app.entry.bind('<Return>',self.enter)
        app.entry.bind('<Control-Return>',self.newline)
        app.entry.bind('<Shift-Return>',self.newline)

    def enter(self,event=None):
        if ime_composing(self.app.entry):return 'break'
        return self.app.send(event)

    def newline(self,event=None):
        entry=self.app.entry
        if ime_composing(entry):return 'break'
        if entry.cget('state') != 'disabled':
            if entry.tag_ranges('sel'):entry.delete('sel.first','sel.last')
            entry.insert('insert','\n');entry.see('insert')
        return 'break'

    def paste(self,event=None):
        try:data=clipboard_image()
        except (ValueError,OSError,subprocess.TimeoutExpired) as exc:
            self.app.status.set(str(exc));return 'break'
        if data is None:return None
        if self.app.busy or self.app.closing:
            self.app.status.set('処理が終わってから画像を貼り付けてください。');return 'break'
        try:
            full=tk.PhotoImage(master=self.app.root,data=base64.b64encode(data))
            scale=max(1,(max(full.width(),full.height())+79)//80)
            preview=full.subsample(scale,scale)
        except tk.TclError:
            self.app.status.set('画像のプレビューを作成できませんでした。');return 'break'
        self.data=data;self.preview=preview;self.picture.configure(image=preview)
        self.bar.grid(row=4,column=0,sticky='ew',pady=4)
        self.app.status.set('画像を添付しました。質問を入力してEnterで送信できます。')
        return 'break'

    def clear(self):
        self.data=None;self.preview=None;self.picture.configure(image='');self.bar.grid_remove()

    def send_image(self):
        if self.data is None:return False
        app=self.app
        if app.busy or app.closing:return True
        question=app.entry.get('1.0','end-1c').strip() or 'この画像の内容を説明してください。'
        if len(question)>2000:
            app.status.set('画像への質問は2000文字以内にしてください。');return True
        data=self.data
        model='gemma3:4b' if 'gemma3:4b' in app.models else app.model.get()
        demo=app.service is not None and app.service.demo
        work=lambda:('画面確認用：画像は送信していません。' if demo else answer_image_bytes(data,question,model))
        if app.submit('reply',work,'貼り付けた画像をローカルAIで読み取っています…'):
            app.append('あなた',question+'\n［貼り付け画像1枚］')
            app.entry.delete('1.0','end');self.clear()
        return True
