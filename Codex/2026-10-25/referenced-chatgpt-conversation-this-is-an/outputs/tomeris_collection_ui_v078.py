import tkinter as tk
from tkinter import ttk,messagebox
from tkinter.scrolledtext import ScrolledText
from tomeris_experience_summary import format_summary
class CollectionPanel:
    def __init__(self,app):
        self.app=app;self.window=tk.Toplevel(app.root);self.window.title('自動資料収集の設定');self.window.geometry('720x600');self.window.minsize(600,480)
        self.window.columnconfigure(0,weight=1);self.window.rowconfigure(3,weight=1);self.window.protocol('WM_DELETE_WINDOW',self.close)
        ttk.Label(self.window,text='Wikipediaへ送る追加テーマ（1行1件・最大3件）\n個人情報を入れず、公開記事の対象名を指定してください。').grid(row=0,column=0,sticky='w',padx=16,pady=12)
        self.topics=tk.Text(self.window,height=4,width=1,wrap='word');self.topics.grid(row=1,column=0,sticky='ew',padx=16)
        self.status=tk.StringVar();ttk.Label(self.window,textvariable=self.status,wraplength=650).grid(row=2,column=0,sticky='w',padx=16,pady=10)
        self.results=ScrolledText(self.window,height=4,width=1,wrap='word',state='disabled');self.results.grid(row=3,column=0,sticky='nsew',padx=16)
        bar=ttk.Frame(self.window);bar.grid(row=4,column=0,sticky='ew',padx=16,pady=12)
        self.buttons=[]
        for title,fn in [('テーマを保存',self.save),('停止',lambda:self.toggle(False)),('再開',lambda:self.toggle(True)),('読み直す',self.load),('閉じる',self.close)]:
            b=ttk.Button(bar,text=title,command=fn);b.pack(side='left',padx=3);self.buttons.append(b)
        self.load()
    def state(self):
        if not self.window.winfo_exists():return
        state='disabled' if self.app.busy or self.app.closing else 'normal'
        for b in self.buttons:b.configure(state=state)
        self.topics.configure(state=state)
    def job(self,fn):
        if self.app.busy or self.app.closing:return
        def work():
            try:fn();result=(None,self.app.service.collection_state())
            except (ValueError,OSError,UnicodeError) as exc:result=(str(exc),self.app.service.collection_state())
            return done,result
        def done(result):
            error,data=result;self.show(data)
            if error:self.status.set('失敗：'+error)
        self.app.submit('plan_result',work,'収集設定を確認しています…');self.state()
    def load(self):self.job(lambda:None)
    def show(self,data):
        self.topics.configure(state='normal');self.topics.delete('1.0','end');self.topics.insert('1.0','\n'.join(data['topics']))
        self.status.set(('有効' if data['enabled'] else '停止中')+f" / 今回の起動で {data['attempts']}/12 試行。間隔10分以上。\n保存すると停止します。再開は明示操作です。"+data['error'])
        text='標準テーマ：'+' ／ '.join(data['standard_topics'])+'\n次の対象：'+(' ／ '.join(data['next_topics']) or '待機中')+'\n保存済みは7日・試行済みは24時間空けます。\n\n今回の起動中の収集結果（資料は未検証）\n'+'\n\n'.join(r['topic']+'\n'+r['status']+'\n'+r['url'] for r in data['results'])
        labels={'exact':'対象名の完全一致','normalized':'中点・全半角の表記違いを許容'}
        text+='\n\n取得経験：'+str(data.get('adaptive_attempts',0))+'件（最大500件）\n基本の優先順：'+' → '.join(labels[a] for a in data.get('adaptive_order',[]))+'\n定期的に元の順序も試します。\n'+format_summary(data.get('adaptive_outcomes',{}))
        self.results.configure(state='normal');self.results.delete('1.0','end');self.results.insert('1.0',text);self.results.configure(state='disabled');self.state()
    def save(self):
        topics=[line.strip() for line in self.topics.get('1.0','end').splitlines() if line.strip()]
        if messagebox.askyesno('テーマの確認','再開後、標準12テーマに加えてWikipediaへ次のテーマを送信します。\n\n'+'\n'.join(topics)+'\n\n保存して収集を停止しますか？',parent=self.window):
            self.job(lambda:self.app.service.save_collection_topics(topics))
    def toggle(self,enabled):
        if enabled and not messagebox.askyesno('自動収集の再開','標準12テーマと保存済み追加テーマで外部検索を再開しますか？未保存の編集は送信しません。',parent=self.window):return
        self.job(lambda:self.app.service.set_auto_collection(enabled))
    def close(self):
        if not self.app.busy:self.window.destroy()
