from pathlib import Path
p=Path('outputs/tomeris_history_search_ui.py')
s=p.read_text(encoding='utf-8-sig')
s=s.replace('from tkinter import ttk','from tkinter import ttk, messagebox')
s=s.replace('ConversationPanel','MemoryPanel').replace('会話履歴','長期記憶').replace('一致する会話','一致する記憶')
s=s.replace('質問と回答を検索します。','分類・本文・記憶IDを検索します。').replace('新しく保存された順に表示します。','追加された順の逆順に表示します。')
s=s.replace('find_conversations','find_memories')
s=s.replace("title=(row['user'] or row['tomeris']).replace('\\n',' ')","title=row['text'].replace('\\n',' ')")
s=s.replace("(row['timestamp'] or '日時不明')+'  '+title[:50]","str(row.get('id',''))+' '+str(row.get('category',''))+'  '+title[:50]")
s=s.replace("self.load('',0); self.state()","self.edit_button=ttk.Button(footer,text='本文を修正',command=self.edit); self.edit_button.grid(row=1,column=0,columnspan=2,sticky='w',pady=6)\n        self.editor=None\n        self.load('',0); self.state()")
s=s.replace("        self.previous.configure", "        self.edit_button.configure(state='normal' if active and self.result and self.list.curselection() else 'disabled')\n        if self.editor is not None: self.editor.state()\n        self.previous.configure",1)
old="            self.text('保存日時：'+(row['timestamp'] or '不明')+'\\n\\nあなた：\\n'+row['user']+'\\n\\nトメリス：\\n'+row['tomeris'])"
new="""            value='['+str(row.get('id',''))+'] '+str(row.get('category',''))+'\\n\\n現在の本文：\\n'+row['text']
            for entry in reversed(row.get('edit_history',[]) if isinstance(row.get('edit_history',[]),list) else []):
                if isinstance(entry,dict): value+='\\n\\n変更前（'+str(entry.get('replaced_at',''))+'）：\\n'+str(entry.get('text',''))
            self.text(value)
        self.state()
    def edit(self):
        if self.app.busy or not self.result or not self.list.curselection(): return
        self.editor=MemoryEditor(self,self.result['rows'][self.list.curselection()[0]])"""
assert old in s;s=s.replace(old,new)
s+='''
class MemoryEditor:
    def __init__(self,parent,row):
        self.parent=parent; self.app=parent.app; self.row=row
        self.window=tk.Toplevel(parent.window); self.window.title('長期記憶の本文を修正')
        self.window.geometry('740x650'); self.window.minsize(600,500)
        self.window.transient(parent.window); self.window.grab_set(); self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.columnconfigure(0,weight=1); self.window.rowconfigure(1,weight=1)
        ttk.Label(self.window,text='本文を修正してから保存してください。\\n修正前の文章は変更履歴に残ります。AIには送信しません。',wraplength=540).grid(row=0,column=0,sticky='ew',padx=16,pady=12)
        self.body=ScrolledText(self.window,width=1,height=1,wrap='word',font=('Yu Gothic UI',11))
        self.body.grid(row=1,column=0,sticky='nsew',padx=16,pady=8); self.body.insert('1.0',row['text'])
        self.message=tk.StringVar(value='本文は1〜10000文字。分類・重要度は変更しません。')
        ttk.Label(self.window,textvariable=self.message,wraplength=540).grid(row=2,column=0,sticky='ew',padx=16,pady=8)
        bar=ttk.Frame(self.window); bar.grid(row=3,column=0,sticky='ew',padx=16,pady=12)
        self.save_button=ttk.Button(bar,text='修正を保存',command=self.save); self.save_button.pack(side='left')
        self.cancel_button=ttk.Button(bar,text='閉じる',command=self.close); self.cancel_button.pack(side='right')
    def state(self):
        if not self.window.winfo_exists(): return
        state='disabled' if self.app.busy or self.app.closing else 'normal'
        for widget in (self.body,self.save_button,self.cancel_button): widget.configure(state=state)
    def save(self):
        if self.app.busy or self.app.closing: return
        text=self.body.get('1.0','end-1c'); row=self.row
        def work():
            try: result=(None,self.app.service.edit_memory(row['id'],row['_revision'],text))
            except (ValueError,OSError) as exc: result=(str(exc),None)
            except Exception: result=('保存できませんでした。入力を残しています。',None)
            return saved,result
        def saved(result):
            error,value=result
            if error: self.message.set(error); self.state(); return
            self.app.append('トメリス',value)
            self.window.destroy(); self.parent.window.grab_set()
            self.parent.load(self.parent.query.get(),self.parent.result['offset'])
        self.app.submit('plan_result',work,'記憶の修正を保存しています…'); self.state()
    def close(self):
        if self.app.busy: return
        if self.body.get('1.0','end-1c')!=self.row['text'] and not messagebox.askyesno('未保存の修正','保存せずに閉じますか？',parent=self.window): return
        self.window.destroy(); self.parent.window.grab_set()
'''
Path('outputs/tomeris_memory_edit_ui.py').write_text(s,encoding='utf-8')
p=Path('outputs/tomeris_desktop_v019.py');s=p.read_text(encoding='utf-8-sig').replace('v0.19','v0.20')
s=s.replace('from tomeris_settings import DesktopService as PlanService, choose_startup_model','from tomeris_settings import choose_startup_model\nfrom tomeris_memory_edit import DesktopService as PlanService\nfrom tomeris_memory_edit_ui import MemoryPanel')
s=s.replace("    def view(self,kind):","    def view(self,kind):\n        if kind=='memories':\n            if not self.busy and not self.closing:\n                self.memory_panel=MemoryPanel(self)\n            return")
s=s.replace("        panel=getattr(self,'conversation_panel',None)","        panel=getattr(self,'memory_panel',None)\n        if panel is not None: panel.state()\n        panel=getattr(self,'conversation_panel',None)")
s=s.replace('                        if not conversation_open',"                        memory_open=getattr(self,'memory_panel',None) and self.memory_panel.window.winfo_exists()\n                        if not memory_open and not conversation_open")
Path('outputs/tomeris_desktop_v020.py').write_text(s,encoding='utf-8')
