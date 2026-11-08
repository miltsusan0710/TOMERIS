"""TOMERIS desktop v0.9. Tk UI with a single serialized background worker."""
import argparse
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from tomeris_desktop_service import DesktopService

class TomerisWindow:
    def __init__(self,root,data_dir=None,demo=False):
        self.root=root
        self.root.title('トメリス | Windowsアプリ v0.9'+('（画面確認用）' if demo else ''))
        self.root.geometry('1080x760')
        self.root.minsize(860,600)
        self.root.configure(bg='#eef2f5')
        self.jobs=queue.Queue()
        self.events=queue.Queue()
        self.busy=True
        self.closing=False
        self.service=None
        self.models=[]
        self.controls=[]
        self.model=tk.StringVar(value='qwen2.5:3b')
        self.second_model=tk.StringVar(value='qwen2.5:1.5b')
        self.mode=tk.StringVar(value='会話')
        self.use_memory=tk.BooleanVar(value=False)
        self.status=tk.StringVar(value='記憶を準備しています…')
        self.connection=tk.StringVar(value='ローカルAI・接続確認前')
        self.make_ui()
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.root.after(80,self.poll)
        threading.Thread(target=self.worker,args=(data_dir,demo),daemon=True).start()
    def make_ui(self):
        style=ttk.Style()
        style.theme_use('clam')
        style.configure('TButton',font=('Yu Gothic UI',10),padding=8)
        style.configure('TCombobox',font=('Yu Gothic UI',10),padding=5)
        style.configure('TCheckbutton',background='#eef2f5',font=('Yu Gothic UI',10))
        side=tk.Frame(self.root,bg='#152936',width=200)
        side.pack(side='left',fill='y')
        side.pack_propagate(False)
        tk.Label(side,text='TOMERIS',fg='#f4f8fa',bg='#152936',font=('Segoe UI',23,'bold')).pack(anchor='w',padx=22,pady=(26,0))
        tk.Label(side,text='思考を、次の行動へ。',fg='#a8c4ce',bg='#152936',font=('Yu Gothic UI',10)).pack(anchor='w',padx=22,pady=(4,28))
        buttons=[('記憶を確認','memories'),('会話履歴','history'),('比較の記録','comparisons'),('PC情報','pc'),('基本人格','persona')]
        for label,kind in buttons:
            button=tk.Button(side,text=label,command=lambda k=kind:self.view(k),bg='#223c4b',fg='#ffffff',activebackground='#355568',activeforeground='white',relief='flat',anchor='w',padx=16,pady=11,font=('Yu Gothic UI',11))
            button.pack(fill='x',padx=14,pady=4)
            self.controls.append(button)
        button=ttk.Button(side,text='＋ 長期記憶を追加',command=self.remember)
        button.pack(fill='x',padx=14,pady=(20,4))
        self.controls.append(button)
        tk.Label(side,text='v0.9  •  Ollama\n会話はこのPCに保存',fg='#a8c4ce',bg='#152936',font=('Yu Gothic UI',10),justify='left').pack(side='bottom',anchor='w',padx=22,pady=24)
        main=tk.Frame(self.root,bg='#eef2f5')
        main.pack(side='left',fill='both',expand=True,padx=24,pady=20)
        header=tk.Frame(main,bg='#eef2f5'); header.pack(fill='x')
        tk.Label(header,text='トメリスと話す',bg='#eef2f5',fg='#172d3a',font=('Yu Gothic UI',22,'bold')).pack(side='left')
        refresh=ttk.Button(header,text='接続を確認',command=self.refresh)
        refresh.pack(side='right'); self.controls.append(refresh)
        tk.Label(main,textvariable=self.connection,bg='#eef2f5',fg='#48626f',font=('Yu Gothic UI',10)).pack(anchor='w',pady=(4,14))
        options=tk.Frame(main,bg='#eef2f5'); options.pack(fill='x',pady=(0,12))
        self.mode_box=ttk.Combobox(options,textvariable=self.mode,values=['会話','2モデル比較'],state='readonly',width=13)
        self.mode_box.pack(side='left',padx=(0,8)); self.mode_box.bind('<<ComboboxSelected>>',lambda e:self.control_state())
        self.model_box=ttk.Combobox(options,textvariable=self.model,state='readonly',width=22)
        self.model_box.pack(side='left',padx=(0,8))
        self.second_box=ttk.Combobox(options,textvariable=self.second_model,state='disabled',width=22)
        self.second_box.pack(side='left')
        self.transcript=ScrolledText(main,wrap='word',font=('Yu Gothic UI',11),bg='#ffffff',fg='#243b47',relief='flat',padx=18,pady=16,state='disabled',height=15)
        self.transcript.pack(fill='both',expand=True)
        self.transcript.tag_configure('you',foreground='#087f83',font=('Yu Gothic UI',11,'bold'),spacing1=15)
        self.transcript.tag_configure('assistant',foreground='#172d3a',font=('Yu Gothic UI',11,'bold'),spacing1=15)
        self.transcript.tag_configure('notice',foreground='#657887',font=('Yu Gothic UI',10),spacing1=10)
        self.transcript.tag_configure('body',spacing3=12)
        self.append('トメリス','こんにちは。質問や相談を入力してください。左のボタンから記憶やPC情報も確認できます。')
        self.memory_check=ttk.Checkbutton(main,text='この質問で記憶を参照する',variable=self.use_memory)
        self.memory_check.pack(anchor='w',pady=(12,5))
        self.entry=tk.Text(main,height=3,wrap='word',font=('Yu Gothic UI',11),bg='white',fg='#172d3a',relief='solid',bd=1,padx=10,pady=8)
        self.entry.pack(fill='x')
        self.entry.bind('<Control-Return>',self.send)
        bottom=tk.Frame(main,bg='#eef2f5'); bottom.pack(fill='x',pady=(9,0))
        tk.Label(bottom,text='Enterで改行  /  Ctrl+Enterで送信',bg='#eef2f5',fg='#657887',font=('Yu Gothic UI',9)).pack(side='left')
        self.send_button=tk.Button(bottom,text='送信',command=self.send,bg='#087f83',fg='white',activebackground='#09666a',activeforeground='white',font=('Yu Gothic UI',11,'bold'),relief='flat',padx=28,pady=8)
        self.send_button.pack(side='right'); self.controls.append(self.send_button)
        tk.Label(main,textvariable=self.status,bg='#eef2f5',fg='#48626f',font=('Yu Gothic UI',10),anchor='w').pack(fill='x',pady=(8,0))
        self.control_state()
    def append(self,title,text):
        self.transcript.configure(state='normal')
        tag='you' if title=='あなた' else ('notice' if title=='お知らせ' else 'assistant')
        self.transcript.insert('end',title+'\n',tag)
        self.transcript.insert('end',text+'\n\n','body')
        self.transcript.configure(state='disabled')
        self.transcript.see('end')
    def control_state(self):
        active=not self.busy and not self.closing and self.service is not None
        for control in self.controls:
            control.configure(state='normal' if active else 'disabled')
        for control in (self.mode_box,self.model_box):
            control.configure(state='readonly' if active else 'disabled')
        self.second_box.configure(state='readonly' if active and self.mode.get()=='2モデル比較' else 'disabled')
        self.memory_check.configure(state='normal' if active else 'disabled')
    def submit(self,kind,func,label):
        if self.busy or self.closing or self.service is None:
            return False
        self.busy=True
        self.status.set(label)
        self.control_state()
        self.jobs.put((kind,func))
        return True
    def send(self,event=None):
        if self.busy or self.closing:
            return 'break'
        question=self.entry.get('1.0','end-1c').strip()
        if not question:
            return 'break'
        model=self.model.get(); second=self.second_model.get(); use_memory=self.use_memory.get()
        if self.mode.get()=='2モデル比較':
            if model==second or model not in self.models or second not in self.models:
                messagebox.showinfo('比較するモデル','導入済みの異なる2モデルを選んでください。',parent=self.root)
                return 'break'
            query=('記憶を参照して：' if use_memory else '')+question
            func=lambda:self.service.compare(query,[model,second],lambda s:self.events.put(('progress',s)))
            label='2つのモデルを順に比較しています…'
        else:
            func=lambda:self.service.chat(question,model,use_memory)
            label='回答を準備しています…'
        if self.submit('reply',func,label):
            self.append('あなた',question)
            self.entry.delete('1.0','end')
        return 'break'
    def view(self,kind):
        self.submit('reply',lambda:self.service.view(kind),'記録を読み込んでいます…')
    def refresh(self):
        self.submit('models',self.service.models,'Ollamaの接続を確認しています…')
    def remember(self):
        if self.busy:
            return
        dialog=tk.Toplevel(self.root); dialog.title('長期記憶を追加'); dialog.geometry('500x310'); dialog.transient(self.root); dialog.grab_set()
        ttk.Label(dialog,text='保存する内容を確認して「保存」を押してください。').pack(anchor='w',padx=18,pady=12)
        category=tk.StringVar(value='その他')
        ttk.Combobox(dialog,textvariable=category,values=['目標','方針','個人設定','決定事項','設計知識','その他'],state='readonly').pack(anchor='w',padx=18)
        body=tk.Text(dialog,height=7,font=('Yu Gothic UI',11),wrap='word'); body.pack(fill='both',expand=True,padx=18,pady=10)
        def save():
            text=body.get('1.0','end-1c').strip(); chosen=category.get()
            if not text:
                return
            dialog.destroy()
            self.submit('reply',lambda:self.service.remember(text,chosen),'長期記憶を保存しています…')
        ttk.Button(dialog,text='保存',command=save).pack(anchor='e',padx=18,pady=(0,12))
        body.focus_set()
    def worker(self,data_dir,demo):
        try:
            service=DesktopService(data_dir=data_dir,demo=demo)
            self.events.put(('ready',service))
        except Exception as exc:
            self.events.put(('fatal',str(exc)))
            return
        while True:
            job=self.jobs.get()
            if job is None:
                service.close()
                self.events.put(('closed',None))
                return
            kind,func=job
            try:
                value=func()
                self.events.put((kind,value))
            except Exception as exc:
                self.events.put(('error',(kind,str(exc))))
    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='ready':
                    self.service=value; self.busy=False
                    if value.imported:
                        self.append('お知らせ','v0.8.4の記憶をデスクトップ版へ引き継ぎました。')
                    self.status.set('準備できました')
                    if not self.closing:
                        self.refresh()
                elif kind=='progress':
                    if not self.closing:
                        self.status.set(value)
                elif kind=='fatal':
                    messagebox.showerror('起動できませんでした',value,parent=self.root)
                    self.root.destroy(); return
                elif kind=='closed':
                    self.root.destroy(); return
                else:
                    self.busy=False
                    if kind=='models':
                        self.models=value
                        self.model_box.configure(values=value); self.second_box.configure(values=value)
                        if value and self.model.get() not in value:
                            self.model.set(value[0])
                        if len(value)>1 and (self.second_model.get() not in value or self.second_model.get()==self.model.get()):
                            self.second_model.set(next(m for m in value if m!=self.model.get()))
                        self.connection.set(f'ローカルAI・{len(value)}モデル確認済み' if value else 'モデル未導入・記憶とPC情報は利用できます')
                    elif kind=='error':
                        failed,error=value
                        if failed=='models':
                            self.connection.set('Ollamaに接続できません・記憶とPC情報は利用できます')
                        self.append('お知らせ',error)
                    else:
                        self.append('トメリス',value)
                    if not self.closing:
                        self.status.set('準備できました')
                        self.entry.focus_set()
                self.control_state()
        except queue.Empty:
            pass
        self.root.after(80,self.poll)
    def close(self):
        if self.closing:
            return
        self.closing=True
        self.status.set('現在の処理と保存が終わったら終了します…')
        self.root.title('トメリス | 終了準備中')
        self.control_state()
        self.jobs.put(None)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--demo',action='store_true',help='画面確認専用。実モデルを呼び出しません')
    parser.add_argument('--data-dir',type=Path)
    args=parser.parse_args()
    if args.demo and args.data_dir is None:
        parser.error('--demo には専用の --data-dir が必要です')
    root=tk.Tk()
    TomerisWindow(root,args.data_dir,args.demo)
    root.mainloop()

if __name__=='__main__':
    main()
