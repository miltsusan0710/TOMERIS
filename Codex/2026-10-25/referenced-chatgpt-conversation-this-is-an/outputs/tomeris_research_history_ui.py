"""Research history browser; loading/filtering never starts a search."""
import tkinter as tk
from tkinter import ttk,messagebox
from tkinter.scrolledtext import ScrolledText

class ResearchHistoryPanel:
    def __init__(self,app):
        self.app=app;self.rows=[];self.visible=[]
        self.window=tk.Toplevel(app.root);self.window.title('調査履歴');self.window.geometry('850x650');self.window.minsize(640,500)
        self.window.columnconfigure(0,weight=1);self.window.rowconfigure(2,weight=1);self.window.rowconfigure(3,weight=2)
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        ttk.Label(self.window,text='過去の調査履歴・最大100件（古い順に自動整理）').grid(row=0,column=0,sticky='w',padx=16,pady=12)
        bar=ttk.Frame(self.window);bar.grid(row=1,column=0,sticky='ew',padx=16);bar.columnconfigure(0,weight=1)
        self.query=tk.StringVar();entry=ttk.Entry(bar,textvariable=self.query);entry.grid(row=0,column=0,sticky='ew');self.entry=entry;self.query.trace_add('write',lambda *_:self.filter())
        self.reload=ttk.Button(bar,text='読み直す',command=self.load);self.reload.grid(row=0,column=1,padx=8)
        frame=ttk.Frame(self.window);frame.grid(row=2,column=0,sticky='nsew',padx=16,pady=8)
        self.list=tk.Listbox(frame,height=4,width=1,exportselection=False);self.list.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(frame,command=self.list.yview);scroll.pack(side='right',fill='y');self.list.configure(yscrollcommand=scroll.set)
        self.list.bind('<<ListboxSelect>>',lambda _:self.select())
        self.detail=ScrolledText(self.window,height=4,width=1,wrap='word',state='disabled');self.detail.grid(row=3,column=0,sticky='nsew',padx=16,pady=8)
        self.message=tk.StringVar(value='履歴を読み込んでいます…');ttk.Label(self.window,textvariable=self.message,wraplength=600).grid(row=4,column=0,sticky='w',padx=16,pady=5)
        bar=ttk.Frame(self.window);bar.grid(row=5,column=0,sticky='ew',padx=16,pady=12)
        self.retry=ttk.Button(bar,text='内容を確認して再調査',command=self.retry_selected);self.retry.pack(side='left')
        self.delete=ttk.Button(bar,text='選択した履歴を削除',command=self.delete_selected);self.delete.pack(side='left',padx=8)
        self.exit=ttk.Button(bar,text='閉じる',command=self.close);self.exit.pack(side='right')
        self.load()
    def state(self):
        if not self.window.winfo_exists():return
        active=not self.app.busy and not self.app.closing
        for w in (self.reload,self.retry,self.delete,self.exit,self.list,self.entry):w.configure(state='normal' if active else 'disabled')
    def job(self,fn,done,label):
        if self.app.busy or self.app.closing:return
        def work():
            try:result=(None,fn())
            except (ValueError,OSError,UnicodeError) as exc:result=(str(exc),None)
            return ready,result
        def ready(result):
            if not self.window.winfo_exists():return
            error,value=result
            if error:self.message.set('処理できませんでした：'+error)
            else:done(value)
            self.state()
        if self.app.submit('plan_result',work,label):self.message.set(label);self.state()
    def load(self):
        def loaded(rows):self.rows=list(reversed(rows));self.filter()
        self.job(lambda:self.app.service.research_journal.read(),loaded,'履歴を読み込んでいます…')
    def filter(self):
        query=self.query.get().strip().casefold()
        self.visible=[r for r in self.rows if query in (r['question']+' '+r['method']+' '+' '.join(s['title']+' '+s['url'] for s in r['sources'])).casefold()]
        self.list.delete(0,'end')
        for r in self.visible:self.list.insert('end',r['retrieved_at']+' / '+r['question'].replace('\n',' ')[:90])
        self.message.set(f'{len(self.visible)}件。閲覧だけでは外部へ送信しません。')
        if self.visible:self.list.selection_set(0)
        self.select()
    def selected(self):
        indices=self.list.curselection();return self.visible[indices[0]] if indices else None
    def select(self):
        row=self.selected();lines=['過去の記録です。今回は再取得していません。']
        if row:
            lines.extend(['質問：'+row['question'],'記録時刻：'+row['retrieved_at'],row['method']])
            for s in row['sources']:lines.extend([s['title'],s['url']])
            lines.append('本文・AI回答は保存していません。現在の内容や正確さは未確認です。')
        else:lines.append('該当する履歴はありません。')
        self.detail.configure(state='normal');self.detail.delete('1.0','end');self.detail.insert('end','\n\n'.join(lines));self.detail.configure(state='disabled')
    def delete_selected(self):
        row=self.selected()
        if not row or self.app.busy:return
        if not messagebox.askyesno('履歴の削除',row['question']+'\nこの調査履歴だけを削除しますか？',parent=self.window):return
        self.job(lambda:self.app.service.research_journal.delete(row['id']),lambda _:self.load(),'履歴を削除しています…')
    def retry_selected(self):
        row=self.selected()
        if not row or self.app.busy:return
        def prepare():
            text=self.app.service.chat('/research-retry '+row['id'],'unused')
            review=self.app.service.retry_review
            return text,review['token'] if review else None
        def prepared(value):
            text,token=value
            if not token:self.message.set(text);return
            prompt=text.split('\n実行：',1)[0]+'\n\nこの内容を送信して再調査しますか？'
            if not messagebox.askyesno('再調査の確認',prompt,parent=self.window):return
            def finished(answer):
                self.app.append('トメリス',answer);self.message.set('再調査の結果を会話欄に表示しました。');self.load()
            self.job(lambda:self.app.service.chat('/research-confirm '+token,'unused'),finished,'確認した質問で再調査しています…')
        self.job(prepare,prepared,'再調査する内容を確認しています…')
    def close(self):
        if not self.app.busy:self.window.destroy()
