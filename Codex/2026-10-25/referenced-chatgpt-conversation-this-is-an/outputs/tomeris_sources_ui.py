import tkinter as tk
from tkinter import ttk,messagebox,font
from tkinter.scrolledtext import ScrolledText

class SourcesPanel:
    def __init__(self,app):
        self.app=app;self.rows={}
        self.window=tk.Toplevel(app.root);self.window.title('保存資料の管理');self.window.geometry('820x700');self.window.minsize(640,580)
        self.window.transient(app.root);self.window.grab_set();self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.columnconfigure(0,weight=1);self.window.rowconfigure(2,weight=1);self.window.rowconfigure(3,weight=2)
        ttk.Label(self.window,text='保存資料（未検証）',font=('Yu Gothic UI',14,'bold')).grid(row=0,column=0,sticky='w',padx=14,pady=10)
        top=ttk.Frame(self.window);top.grid(row=1,column=0,sticky='ew',padx=14,pady=4);top.columnconfigure(0,weight=1)
        self.query=ttk.Entry(top,width=1);self.query.grid(row=0,column=0,sticky='ew');self.query.bind('<Return>',lambda e:self.reload())
        self.search=ttk.Button(top,text='検索・再読込',command=self.reload);self.search.grid(row=0,column=1,padx=(6,0))
        listing=ttk.Frame(self.window);listing.grid(row=2,column=0,sticky='nsew',padx=14,pady=6);listing.columnconfigure(0,weight=1);listing.rowconfigure(0,weight=1)
        tree_font=font.Font(self.window,family='Yu Gothic UI',size=10)
        ttk.Style(self.window).configure('Sources.Treeview',font=tree_font,rowheight=tree_font.metrics('linespace')+8)
        self.tree_font=tree_font
        self.tree=ttk.Treeview(listing,style='Sources.Treeview',columns=('title',),show='headings',height=2,selectmode='browse');self.tree.heading('title',text='資料名（取得日時・URLは下に表示）');self.tree.column('title',width=400,minwidth=100)
        self.tree.grid(row=0,column=0,sticky='nsew');scroll=ttk.Scrollbar(listing,orient='vertical',command=self.tree.yview);scroll.grid(row=0,column=1,sticky='ns');self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind('<<TreeviewSelect>>',lambda e:self.show_selected())
        self.detail=ScrolledText(self.window,width=1,height=2,wrap='word',state='disabled',font=('Yu Gothic UI',10));self.detail.grid(row=3,column=0,sticky='nsew',padx=14,pady=4)
        self.message=tk.StringVar(value='読み込み中…');ttk.Label(self.window,textvariable=self.message,wraplength=570,font=('Yu Gothic UI',9)).grid(row=4,column=0,sticky='ew',padx=14,pady=6)
        footer=ttk.Frame(self.window);footer.grid(row=5,column=0,sticky='ew',padx=14,pady=(0,12));footer.columnconfigure(1,weight=1)
        self.check=ttk.Button(footer,text='URLを再取得して確認',command=self.check_selected);self.check.grid(row=0,column=0,sticky='w')
        self.delete=ttk.Button(footer,text='選択資料を消去',command=self.delete_selected);self.delete.grid(row=1,column=0,sticky='w',pady=(6,0))
        self.exit=ttk.Button(footer,text='閉じる',command=self.close);self.exit.grid(row=1,column=1,sticky='e')
        self.reload()
    def selected(self):
        selected=self.tree.selection();return self.rows.get(selected[0]) if selected else None
    def state(self):
        if not self.window.winfo_exists():return
        active=not self.app.busy and not self.app.closing
        for w in (self.query,self.search,self.exit):w.configure(state='normal' if active else 'disabled')
        for w in (self.check,self.delete):w.configure(state='normal' if active and self.selected() else 'disabled')
    def text(self,value):
        self.detail.configure(state='normal');self.detail.delete('1.0','end');self.detail.insert('end',value);self.detail.configure(state='disabled')
    def show_selected(self):
        row=self.selected()
        self.text(('未検証の保存資料\n'+row['title']+'\n'+row['url']+'\n保存時の取得日時：'+row['retrieved']+'\n\n再取得状態：'+row['check']+'\n\n保存時の抜粋（現在の情報とは限りません）\n'+row['excerpt']) if row else '一覧から資料を選択してください。')
        self.state()
    def run(self,operation,callback):
        if self.app.busy or self.app.closing:return
        def work():
            try:result=(None,operation())
            except (ValueError,OSError) as exc:result=(str(exc),None)
            except Exception:result=('資料の操作を完了できませんでした。',None)
            return completed,result
        def completed(result):
            error,value=result
            if error:self.message.set(error)
            else:callback(value)
            self.state()
        self.app.submit('plan_result',work,'保存資料を確認しています…');self.state()
    def reload(self):
        query=self.query.get().strip();selected=self.selected();url=selected['url'] if selected else None
        def loaded(data):
            self.tree.delete(*self.tree.get_children());self.rows={}
            for i,row in enumerate(data['rows']):
                key=str(i);self.rows[key]=row;self.tree.insert('', 'end',iid=key,values=(row['title'] or row['url'],))
                if row['url']==url:self.tree.selection_set(key)
            self.message.set(data['error'] or f"{len(data['rows'])}件表示 / 全{data['total']}件。資料学習："+('有効' if data['enabled'] else '停止中'))
            self.show_selected()
        self.run(lambda:self.app.service.source_records(query),loaded)
    def check_selected(self):
        row=self.selected()
        if not row:return
        def checked(status):
            row['check']=self.app.service.source_checks.get(row['url'],status);self.show_selected();self.message.set('再取得の結果を詳細欄に表示しました。')
        self.run(lambda:self.app.service.check_source(row['url'],row['revision']),checked)
    def delete_selected(self):
        row=self.selected()
        if not row or not messagebox.askyesno('保存資料の消去','この資料だけを消去しますか？\n'+row['title'],parent=self.window):return
        def deleted(status):
            key=next(k for k,r in self.rows.items() if r['url']==row['url']);self.tree.delete(key);self.rows.pop(key);self.show_selected();self.message.set(status)
        self.run(lambda:self.app.service.remove_source(row['url'],row['revision']),deleted)
    def close(self):
        if not self.app.busy:self.window.destroy()

