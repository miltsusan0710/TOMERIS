"""Explicit review selection and split UI. No automatic reward or model updates."""
import re
from pathlib import Path
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from tkinter.scrolledtext import ScrolledText
from tomeris_trial_export import read,child,export

def inventory(directory):
    root=Path(directory).resolve();rows=[];skipped=0
    if not root.exists():return rows,skipped
    paths=[]
    for path in root.glob('*.review.*.json'):
        paths.append(path)
        if len(paths)>1000:raise ValueError('評価記録が1000件を超えています。先に整理してください。')
    for path in sorted(paths):
        try:
            review=read(child(root,path.name));trial=review.get('trial_id','')
            if not isinstance(trial,str) or not re.fullmatch('[a-f0-9]{32}',trial):raise ValueError('ID')
            record_name=trial+'.json';record=read(child(root,record_name))['record']
            if record.get('id')!=trial or not isinstance(record.get('question'),str):raise ValueError('形式')
            rows.append(dict(record=record_name,review=path.name,question=record['question'],context=record.get('context','不明'),
                             date=str(review.get('reviewed_at','不明')),reason=str(review.get('reason','')),ratings=review.get('ratings',{})))
        except (OSError,ValueError,KeyError,TypeError,AttributeError):skipped+=1
    return rows,skipped

class DatasetPanel:
    def __init__(self,app):
        self.app=app;self.directory=app.service.data_dir/'research_trials';self.rows=[];self.selected={}
        self.window=tk.Toplevel(app.root);self.window.title('採点済み資料を学習用・評価用に分ける');self.window.geometry('980x720');self.window.minsize(720,580)
        self.window.columnconfigure(0,weight=1);self.window.rowconfigure(1,weight=1);self.window.rowconfigure(2,weight=1)
        ttk.Label(self.window,text='採用する評価を選び、対象グループと用途を指定してください。初期状態では何も採用しません。\n同じ対象の別名にも同じグループ名を指定。学習と評価の両方に「概要」「具体的質問」が必要です。',wraplength=880).grid(row=0,column=0,sticky='ew',padx=12,pady=10)
        frame=ttk.Frame(self.window);frame.grid(row=1,column=0,sticky='nsew',padx=12);frame.columnconfigure(0,weight=1);frame.rowconfigure(0,weight=1)
        self.tree=ttk.Treeview(frame,columns=('use','question','context','group','date'),show='headings',selectmode='browse',height=7)
        for name,title,width in [('use','用途',65),('question','質問',290),('context','種類',90),('group','対象グループ',150),('date','採点日時',170)]:
            self.tree.heading(name,text=title);self.tree.column(name,width=width,minwidth=55,stretch=True)
        self.tree.grid(row=0,column=0,sticky='nsew');scroll=ttk.Scrollbar(frame,command=self.tree.yview);scroll.grid(row=0,column=1,sticky='ns');self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind('<<TreeviewSelect>>',self.show)
        self.details=ScrolledText(self.window,height=6,wrap='word',state='disabled',font=('Yu Gothic UI',10));self.details.grid(row=2,column=0,sticky='nsew',padx=12,pady=8)
        edit=ttk.Frame(self.window);edit.grid(row=3,column=0,sticky='ew',padx=12)
        ttk.Label(edit,text='対象グループ').grid(row=0,column=0);self.group=ttk.Entry(edit,width=24);self.group.grid(row=0,column=1,padx=6)
        self.split=tk.StringVar(value='学習用');ttk.Combobox(edit,textvariable=self.split,values=['学習用','評価用'],state='readonly',width=10).grid(row=0,column=2,padx=6)
        ttk.Button(edit,text='この評価を採用',command=self.include).grid(row=1,column=0,columnspan=2,sticky='w',pady=8)
        ttk.Button(edit,text='採用を取り消す',command=self.exclude).grid(row=1,column=2,columnspan=2,sticky='w',pady=8)
        self.status=tk.StringVar(value='');ttk.Label(self.window,textvariable=self.status,wraplength=850).grid(row=4,column=0,sticky='ew',padx=12,pady=8)
        bar=ttk.Frame(self.window);bar.grid(row=5,column=0,sticky='ew',padx=12,pady=10)
        self.write=ttk.Button(bar,text='検査して新規ファイルに書き出す',command=self.save);self.write.pack(side='left')
        ttk.Label(bar,text='  書き出しだけでは学習・本番適用しません。').pack(side='left')
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.load()
    def load(self):
        def work():
            try:result=(inventory(self.directory),None)
            except (OSError,ValueError) as exc:result=(None,str(exc))
            return done,result
        def done(result):
            if not self.window.winfo_exists():return
            data,error=result
            if error:self.status.set(error);return
            self.rows,skipped=data
            for i,row in enumerate(self.rows):self.tree.insert('', 'end',iid=str(i),values=('未採用',row['question'],row['context'],'',row['date']))
            self.status.set(f'{len(self.rows)}件の評価。未読込 {skipped}件。ハッシュや本文は書き出し時に検査します。')
        self.app.submit('plan_result',work,'評価記録の一覧を読み込んでいます…')
    def current(self):
        selected=self.tree.selection();return int(selected[0]) if selected else None
    def show(self,event=None):
        index=self.current()
        if index is None:return
        row=self.rows[index];choice=self.selected.get(index)
        self.group.delete(0,'end');self.group.insert(0,choice['topic_id'] if choice else '')
        self.split.set('評価用' if choice and choice['split']=='test' else '学習用')
        text=f"質問：{row['question']}\n種類：{row['context']}\n評価ファイル：{row['review']}\n点数：{row['ratings']}\n理由：{row['reason']}\n\n訂正評価が複数ある場合は、そのうち一つだけ採用してください。"
        self.details.configure(state='normal');self.details.delete('1.0','end');self.details.insert('1.0',text);self.details.configure(state='disabled')
    def include(self):
        if self.app.busy or self.app.closing:return
        index=self.current();group=self.group.get().strip()
        if index is None:return
        if not 1<=len(group)<=100:self.status.set('対象グループを1〜100文字で入力してください。');return
        row=self.rows[index]
        if any(i!=index and s['record']==row['record'] for i,s in self.selected.items()):self.status.set('同じ試行の評価が採用済みです。先に取り消してください。');return
        self.selected[index]=dict(record=row['record'],review=row['review'],topic_id=group,split='test' if self.split.get()=='評価用' else 'train')
        self.tree.set(str(index),'use',self.split.get());self.tree.set(str(index),'group',group);self.status.set(f'{len(self.selected)}件採用。まだ書き出していません。')
    def exclude(self):
        if self.app.busy or self.app.closing:return
        index=self.current()
        if index is None:return
        self.selected.pop(index,None);self.tree.set(str(index),'use','未採用');self.tree.set(str(index),'group','');self.status.set(f'{len(self.selected)}件採用。')
    def save(self):
        if self.app.busy or self.app.closing:return
        if len(self.selected)<4:self.status.set('4件以上を採用してください。各用途に概要と具体的質問が必要です。');return
        path=filedialog.asksaveasfilename(parent=self.window,title='学習・評価データを新規保存',defaultextension='.json',initialfile='reviewed_dataset.json',filetypes=[('JSON','*.json')],confirmoverwrite=False)
        if path:self.write_to(path)
    def write_to(self,path):
        if self.app.busy or self.app.closing:return
        manifest=[dict(v) for v in self.selected.values()]
        def work():
            try:result=(export(self.directory,manifest,path),None)
            except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:result=(None,str(exc))
            return done,result
        def done(result):
            if not self.window.winfo_exists():return
            count,error=result
            self.status.set('書き出しを止めました：'+error if error else f'{count}件を書き出しました。学習・通常回答への反映はしていません。保存先：{path}')
        self.app.submit('plan_result',work,'採点と学習／評価の分離を検査しています…')
    def close(self):
        if not self.app.busy:self.window.destroy()
