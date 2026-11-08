"""Memory history selection only stages text; saving uses the existing atomic edit path."""
from tkinter import ttk, messagebox
from tomeris_memory_edit_ui import MemoryPanel as BasePanel, MemoryEditor as BaseEditor

class MemoryPanel(BasePanel):
    def edit(self):
        if self.app.busy or self.app.closing or not self.result or not self.list.curselection(): return
        self.editor=MemoryEditor(self,self.result['rows'][self.list.curselection()[0]])

class MemoryEditor(BaseEditor):
    def __init__(self,parent,row):
        super().__init__(parent,row)
        self.window.geometry('760x740'); self.window.minsize(600,640)
        self.window.rowconfigure(1,weight=0); self.window.rowconfigure(2,weight=1)
        # Move existing rows from the bottom upward before inserting the history bar.
        for widget in self.window.grid_slaves():
            position=int(widget.grid_info()['row'])
            if position>=1: widget.grid_configure(row=position+1)
        bar=ttk.Frame(self.window); bar.grid(row=1,column=0,sticky='ew',padx=16,pady=8)
        bar.columnconfigure(0,weight=1)
        ttk.Label(bar,text='以前の文章を選ぶ（保存するまで反映されません）',wraplength=540).grid(row=0,column=0,columnspan=2,sticky='w')
        self.versions=[row['text']]; labels=['現在保存されている文章']
        history=row.get('edit_history',[])
        if isinstance(history,list):
            for index,entry in reversed(list(enumerate(history,1))):
                if isinstance(entry,dict) and isinstance(entry.get('text'),str):
                    self.versions.append(entry['text'])
                    labels.append(f"変更前 {index} | {entry.get('replaced_at','日時不明')}")
        self.version=ttk.Combobox(bar,values=labels,state='readonly',width=1)
        self.version.grid(row=1,column=0,sticky='ew',pady=8); self.version.current(0)
        self.load_button=ttk.Button(bar,text='本文に読み込む',command=self.stage)
        self.load_button.grid(row=1,column=1,padx=(8,0))
        if len(self.versions)==1: self.message.set('変更履歴はまだありません。本文を修正して保存すると履歴が残ります。')
        self.state()
    def state(self):
        super().state()
        if not self.window.winfo_exists() or not hasattr(self,'version'): return
        active=not self.app.busy and not self.app.closing
        self.version.configure(state='readonly' if active else 'disabled')
        self.load_button.configure(state='normal' if active else 'disabled')
    def stage(self):
        if self.app.busy or self.app.closing: return
        index=self.version.current()
        if index<0 or index>=len(self.versions): return
        text=self.versions[index]; current=self.body.get('1.0','end-1c')
        if current==text: return
        if current!=self.row['text'] and not messagebox.askyesno('未保存の文章', '編集中の文章を、選んだ文章に置き換えますか？',parent=self.window): return
        self.body.delete('1.0','end'); self.body.insert('1.0',text)
        self.message.set('選んだ文章を読み込みました。内容を確認して「修正を保存」を押してください。まだ保存していません。')
        self.body.focus_set()
