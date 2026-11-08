"""Plan reflection editor with explicit save and failed-write preservation."""
import tkinter as tk
from tkinter import ttk,messagebox
from tkinter.scrolledtext import ScrolledText

class ReflectionPanel:
    def __init__(self,history,identifier):
        self.history=history; self.app=history.app; self.identifier=identifier; self.saved=None
        self.window=tk.Toplevel(history.window); self.window.title('計画の振り返り')
        self.window.geometry('700x560'); self.window.minsize(580,500)
        self.window.transient(history.window); self.window.grab_set()
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.columnconfigure(0,weight=1); self.window.rowconfigure(2,weight=1)
        self.heading=tk.StringVar(value='振り返りを読み込んでいます…')
        ttk.Label(self.window,textvariable=self.heading,wraplength=510,font=('Yu Gothic UI',12,'bold')).grid(row=0,column=0,sticky='ew',padx=18,pady=12)
        ttk.Label(self.window,text='例：できたこと／難しかったこと／次に変えること\n自由に書けます（2000文字まで）。保存するまで記録は変わりません。',wraplength=510).grid(row=1,column=0,sticky='ew',padx=18,pady=6)
        self.body=ScrolledText(self.window,width=1,height=1,font=('Yu Gothic UI',11),wrap='word',state='disabled')
        self.body.grid(row=2,column=0,sticky='nsew',padx=18,pady=8)
        self.notice=tk.StringVar(value='読込中…')
        ttk.Label(self.window,textvariable=self.notice,wraplength=510).grid(row=3,column=0,sticky='ew',padx=18,pady=6)
        actions=ttk.Frame(self.window); actions.grid(row=4,column=0,sticky='ew',padx=18,pady=(0,14))
        self.save_button=ttk.Button(actions,text='振り返りを保存',command=self.save); self.save_button.pack(side='left')
        self.exit_button=ttk.Button(actions,text='閉じる',command=self.close); self.exit_button.pack(side='right')
        self.run(lambda:self.app.service.get_reflection(identifier),self.loaded,'振り返りを読み込んでいます…')
        self.state()
    def state(self):
        if not self.window.winfo_exists(): return
        active=not self.app.busy and not self.app.closing
        self.body.configure(state='normal' if active and self.saved is not None else 'disabled')
        self.save_button.configure(state='normal' if active and self.saved is not None else 'disabled')
        self.exit_button.configure(state='normal' if active else 'disabled')
    def run(self,operation,callback,label):
        if self.app.busy or self.app.closing: return
        def work():
            try: result=(None,operation())
            except (ValueError,OSError) as exc: result=(str(exc),None)
            except Exception: result=('振り返りの処理を完了できませんでした。',None)
            return completed,result
        def completed(result):
            if not self.window.winfo_exists(): return
            error,value=result
            if error: self.notice.set('処理に失敗しました：'+error)
            else: callback(value)
            self.state()
        if self.app.submit('plan_result',work,label):
            self.notice.set(label); self.state()
    def loaded(self,value):
        self.saved=value
        goal=value['goal'] if len(value['goal'])<=40 else value['goal'][:40]+'…'
        self.heading.set(value['date']+' / '+goal)
        self.body.configure(state='normal'); self.body.delete('1.0','end'); self.body.insert('1.0',value['text'])
        self.notice.set('内容を確認して「振り返りを保存」を押してください。')
    def save(self):
        if self.saved is None or self.app.busy: return
        text=self.body.get('1.0','end-1c'); revision=self.saved['revision']
        def saved(value):
            self.saved=value
            self.body.configure(state='normal'); self.body.delete('1.0','end'); self.body.insert('1.0',value['text'])
            for row in self.history.rows:
                if row['id']==self.identifier: row['reflection']=value['text']
            self.history.select()
            self.notice.set('振り返りを保存しました。計画の履歴から見返せます。')
        self.run(lambda:self.app.service.save_reflection(self.identifier,text,revision),saved,'振り返りを保存しています…')
    def close(self):
        if self.app.busy:
            self.notice.set('処理が終わるまでお待ちください。'); return
        if self.saved is not None and self.body.get('1.0','end-1c').strip()!=self.saved['text']:
            if not messagebox.askyesno('未保存の振り返り','入力した変更を保存せずに閉じますか？',parent=self.window): return
        self.window.destroy()
        if self.history.window.winfo_exists():
            self.history.window.grab_set(); self.history.window.focus_set()
