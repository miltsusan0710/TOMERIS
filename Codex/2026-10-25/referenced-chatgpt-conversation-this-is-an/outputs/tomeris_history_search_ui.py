import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

class ConversationPanel:
    def __init__(self,app):
        self.app=app; self.result=None
        self.window=tk.Toplevel(app.root); self.window.title('会話履歴を検索')
        self.window.geometry('820x700'); self.window.minsize(640,580)
        self.window.transient(app.root); self.window.grab_set(); self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.columnconfigure(0,weight=1); self.window.rowconfigure(4,weight=1)
        ttk.Label(self.window,text='会話履歴を検索',font=('Yu Gothic UI',17,'bold')).grid(row=0,column=0,sticky='w',padx=18,pady=12)
        bar=ttk.Frame(self.window); bar.grid(row=1,column=0,sticky='ew',padx=18,pady=6); bar.columnconfigure(0,weight=1)
        self.query=tk.StringVar()
        self.entry=ttk.Entry(bar,textvariable=self.query,width=1); self.entry.grid(row=0,column=0,sticky='ew')
        self.entry.bind('<Return>',self.search)
        self.search_button=ttk.Button(bar,text='検索',command=self.search); self.search_button.grid(row=0,column=1,padx=6)
        self.clear_button=ttk.Button(bar,text='すべて表示',command=self.clear); self.clear_button.grid(row=0,column=2)
        ttk.Label(self.window,text='質問と回答を検索します。空白で区切ると、すべての語を含む会話を探します。\n英字の大小・全角半角は区別しません。新しく保存された順に表示します。',wraplength=580).grid(row=2,column=0,sticky='ew',padx=18,pady=6)
        area=ttk.Frame(self.window); area.grid(row=3,column=0,sticky='ew',padx=18,pady=6)
        self.list=tk.Listbox(area,height=3,width=1,exportselection=False,font=('Yu Gothic UI',10))
        self.list.pack(side='left',fill='both',expand=True)
        scrollbar=ttk.Scrollbar(area,orient='vertical',command=self.list.yview); scrollbar.pack(side='right',fill='y')
        self.list.configure(yscrollcommand=scrollbar.set); self.list.bind('<<ListboxSelect>>',lambda e:self.select())
        self.detail=ScrolledText(self.window,height=1,width=1,wrap='word',state='disabled',font=('Yu Gothic UI',11))
        self.detail.grid(row=4,column=0,sticky='nsew',padx=18,pady=8)
        self.message=tk.StringVar(value='履歴を読み込んでいます…')
        ttk.Label(self.window,textvariable=self.message,wraplength=580).grid(row=5,column=0,sticky='ew',padx=18,pady=6)
        footer=ttk.Frame(self.window); footer.grid(row=6,column=0,sticky='ew',padx=18,pady=(0,14))
        footer.columnconfigure(2,weight=1)
        self.previous=ttk.Button(footer,text='前の50件',command=lambda:self.page(-1)); self.previous.grid(row=0,column=0)
        self.next=ttk.Button(footer,text='次の50件',command=lambda:self.page(1)); self.next.grid(row=0,column=1,padx=6)
        self.exit_button=ttk.Button(footer,text='閉じる',command=self.close); self.exit_button.grid(row=0,column=3)
        self.load('',0); self.state()
    def state(self):
        if not self.window.winfo_exists(): return
        active=not self.app.busy and not self.app.closing
        for control in [self.entry,self.search_button,self.clear_button,self.list,self.exit_button]:
            control.configure(state='normal' if active else 'disabled')
        self.previous.configure(state='normal' if active and self.result and self.result['offset']>0 else 'disabled')
        self.next.configure(state='normal' if active and self.result and self.result['offset']+self.result['page_size']<self.result['total'] else 'disabled')
    def text(self,value):
        self.detail.configure(state='normal'); self.detail.delete('1.0','end'); self.detail.insert('end',value); self.detail.configure(state='disabled')
    def search(self,event=None):
        self.load(self.query.get(),0)
        return 'break'
    def clear(self):
        if self.app.busy: return
        self.query.set(''); self.load('',0)
    def page(self,direction):
        if self.result:
            self.load(self.result['query'],max(0,self.result['offset']+direction*self.result['page_size']))
    def load(self,query,offset):
        if self.app.busy or self.app.closing: return
        def work():
            try: result=(None,self.app.service.find_conversations(query,offset))
            except (ValueError,OSError) as exc: result=(str(exc),None)
            except Exception: result=('履歴を検索できませんでした。',None)
            return loaded,result
        def loaded(result):
            if not self.window.winfo_exists(): return
            error,value=result
            self.state()
            self.list.delete(0,'end')
            if error:
                self.result=None; self.text('検索できませんでした。'); self.message.set(error)
            else:
                self.result=value
                self.query.set(value["query"])
                for row in value['rows']:
                    title=(row['user'] or row['tomeris']).replace('\n',' ')
                    self.list.insert('end',(row['timestamp'] or '日時不明')+'  '+title[:50]+('…' if len(title)>50 else ''))
                if value['rows']:
                    self.list.selection_set(0); self.select()
                    start=value['offset']+1; end=value['offset']+len(value['rows'])
                    self.message.set(f"{value['total']}件中 {start}〜{end}件を表示。原文を表示しています。")
                else:
                    self.text('一致する会話はありません。検索語を変えるか「すべて表示」を押してください。' if query.strip() else '会話履歴はまだありません。')
                    self.message.set('0件')
            self.state()
        if self.app.submit('plan_result',work,'会話履歴を検索しています…'):
            self.message.set('検索中…'); self.state()
    def select(self):
        selected=self.list.curselection()
        if self.result and selected and selected[0]<len(self.result['rows']):
            row=self.result['rows'][selected[0]]
            self.text('保存日時：'+(row['timestamp'] or '不明')+'\n\nあなた：\n'+row['user']+'\n\nトメリス：\n'+row['tomeris'])
    def close(self):
        if self.app.busy:
            self.message.set('検索が終わるまでお待ちください。'); return
        self.window.destroy()
