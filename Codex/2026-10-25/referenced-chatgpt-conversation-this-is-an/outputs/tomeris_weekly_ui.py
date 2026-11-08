import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tomeris_weekly import format_report

class WeeklyPanel:
    def __init__(self,history):
        self.history=history; self.app=history.app
        self.window=tk.Toplevel(history.window); self.window.title('7日間のまとめ')
        self.window.geometry('760x650'); self.window.minsize(580,460)
        self.window.transient(history.window); self.window.grab_set()
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.columnconfigure(0,weight=1); self.window.rowconfigure(1,weight=1)
        ttk.Label(self.window,text='7日間のまとめ',font=('Yu Gothic UI',17,'bold')).grid(row=0,column=0,sticky='w',padx=18,pady=14)
        self.body=ScrolledText(self.window,width=1,height=1,wrap='word',state='disabled',font=('Yu Gothic UI',11))
        self.body.grid(row=1,column=0,sticky='nsew',padx=18,pady=8)
        self.notice=tk.StringVar(value='記録を読み込んでいます…')
        ttk.Label(self.window,textvariable=self.notice,wraplength=500).grid(row=2,column=0,sticky='ew',padx=18,pady=8)
        footer=ttk.Frame(self.window); footer.grid(row=3,column=0,sticky='ew',padx=18,pady=(0,14))
        self.reload=ttk.Button(footer,text='読み直す',command=self.load); self.reload.pack(side='left')
        self.exit_button=ttk.Button(footer,text='閉じる',command=self.close); self.exit_button.pack(side='right')
        self.load(); self.state()
    def state(self):
        if not self.window.winfo_exists(): return
        active=not self.app.busy and not self.app.closing
        for control in [self.reload,self.exit_button]: control.configure(state='normal' if active else 'disabled')
    def text(self,text):
        self.body.configure(state='normal'); self.body.delete('1.0','end'); self.body.insert('end',text); self.body.configure(state='disabled')
    def load(self):
        if self.app.busy or self.app.closing: return
        def work():
            try: result=(None,format_report(self.app.service.weekly_report()))
            except (ValueError,OSError) as exc: result=(str(exc),None)
            except Exception: result=('記録を読み取れませんでした。',None)
            return loaded,result
        def loaded(result):
            if not self.window.winfo_exists(): return
            error,text=result
            if error:
                self.text('まとめを取得できませんでした。')
                self.notice.set('読込失敗：'+error)
            else:
                self.text(text); self.notice.set('今日を含む7日間です。閲覧では記録を変更しません。')
            self.state()
        if self.app.submit('plan_result',work,'7日間の記録を集計しています…'):
            self.notice.set('記録を読み込んでいます…'); self.state()
    def close(self):
        if self.app.busy:
            self.notice.set('読込が終わるまでお待ちください。'); return
        self.window.destroy()
        if self.history.window.winfo_exists():
            self.history.window.grab_set(); self.history.window.focus_set()
