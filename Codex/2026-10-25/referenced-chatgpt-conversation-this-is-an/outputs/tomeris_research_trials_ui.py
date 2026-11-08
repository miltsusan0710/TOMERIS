import tkinter as tk
from tkinter import ttk,messagebox
from tkinter.scrolledtext import ScrolledText
from tomeris_research_trials import collect,save_record,save_review,render

class TrialPanel:
    def __init__(self,app):
        self.app=app;self.path=None
        self.window=tk.Toplevel(app.root);self.window.title('調査を比較・採点（実験）');self.window.geometry('900x720');self.window.minsize(650,540)
        self.window.columnconfigure(0,weight=1);self.window.rowconfigure(3,weight=1)
        ttk.Label(self.window,text='Wikipediaに公開テーマ名を送信し、最大3記事を取得・ローカル保存します。\n個人情報は入力しないでください。記憶や過去会話は送りません。最新情報の比較には使えません。',wraplength=800).grid(row=0,column=0,sticky='ew',padx=14,pady=10)
        self.query=ttk.Entry(self.window);self.query.grid(row=1,column=0,sticky='ew',padx=14)
        bar=ttk.Frame(self.window);bar.grid(row=2,column=0,sticky='ew',padx=14,pady=8)
        self.context=tk.StringVar(value='概要');ttk.Combobox(bar,textvariable=self.context,values=['概要','具体的質問'],state='readonly',width=14).pack(side='left')
        self.fetch=ttk.Button(bar,text='比較用の資料を取得',command=self.start);self.fetch.pack(side='left',padx=8)
        self.notice=tk.StringVar(value='まだ取得していません');ttk.Label(bar,textvariable=self.notice).pack(side='left')
        self.body=ScrolledText(self.window,wrap='word',state='disabled',font=('Yu Gothic UI',11));self.body.grid(row=3,column=0,sticky='nsew',padx=14)
        controls=ttk.Frame(self.window);controls.grid(row=4,column=0,sticky='ew',padx=14,pady=8)
        self.ratings={}
        for action,label in [('search_order','A 検索順'),('exact_title_first','B 対象名一致優先')]:
            ttk.Label(controls,text=label).pack(side='left');var=tk.StringVar(value='未採点');self.ratings[action]=var
            ttk.Combobox(controls,textvariable=var,values=['未採点','不適合','一部適合','適合'],state='readonly',width=9).pack(side='left',padx=8)
        ttk.Label(self.window,text='採点理由（質問への適合・日時・原文との対応・同名の取り違えなど）').grid(row=5,column=0,sticky='w',padx=14)
        self.reason=tk.Text(self.window,height=3,wrap='word');self.reason.grid(row=6,column=0,sticky='ew',padx=14)
        self.save=ttk.Button(self.window,text='人による評価を別ファイルに保存',command=self.review,state='disabled');self.save.grid(row=7,column=0,sticky='w',padx=14,pady=10)
        self.window.protocol('WM_DELETE_WINDOW',self.close)
    def start(self):
        app=self.app
        if app.busy or app.closing:return
        if app.service.demo:messagebox.showinfo('画面確認用','このモードでは実取得しません。',parent=self.window);return
        question=self.query.get();context='overview' if self.context.get()=='概要' else 'specific'
        self.path=None;self.save.configure(state='disabled');self.fetch.configure(state='disabled');self.notice.set('取得中…')
        for var in self.ratings.values():var.set('未採点')
        self.reason.delete('1.0','end')
        def work():
            try:
                record=collect(question,context);path=save_record(app.service.data_dir/'research_trials',record)
                result=(path,render(record),None)
            except Exception as exc:result=(None,'',str(exc))
            return done,result
        def done(result):
            if not self.window.winfo_exists():return
            self.path,text,error=result;self.fetch.configure(state='normal')
            self.body.configure(state='normal');self.body.delete('1.0','end');self.body.insert('1.0',text or error);self.body.configure(state='disabled')
            self.notice.set('未採点・記録保存済み' if self.path else '取得・保存できませんでした')
            self.save.configure(state='normal' if self.path else 'disabled')
        app.submit('plan_result',work,'比較用の公開資料を取得しています…')
    def review(self):
        if self.app.busy or self.app.closing or not self.path:return
        values={'不適合':-1,'一部適合':0,'適合':1}
        try:
            ratings={k:values.get(v.get()) for k,v in self.ratings.items()}
            save_review(self.path,ratings,self.reason.get('1.0','end'))
        except (ValueError,OSError,KeyError) as exc:messagebox.showerror('採点を保存できません',str(exc),parent=self.window);return
        self.notice.set('評価保存済み・自動学習には未適用');self.save.configure(state='disabled')
    def close(self):
        if not self.app.busy:self.window.destroy()
