"""TOMERIS desktop v0.23. Tk UI with a single serialized background worker."""
import argparse
import re
import webbrowser
from tomeris_web_search import public_url
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timezone, timedelta
from tkinter.scrolledtext import ScrolledText
from tomeris_plans import validate, today
from tomeris_settings import choose_startup_model
from tomeris_web_search import DesktopService as PlanService
from tomeris_memory_restore_ui import MemoryPanel
from tomeris_history_search_ui import ConversationPanel
from tomeris_restore_ui import RestorePanel
from tomeris_plan_history_ui_v015 import PlanHistoryPanel
from tomeris_today_ui import TodayPanel
from tomeris_google import GoogleCalendar
from tomeris_google_ui import GooglePanel

class DesktopService(PlanService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.google=GoogleCalendar(self.data_dir)


class TomerisWindow:
    def __init__(self,root,data_dir=None,demo=False):
        self.root=root
        self.root.title('トメリス | Windowsアプリ v0.23'+('（画面確認用）' if demo else ''))
        self.alternate_data=Path(data_dir).resolve() if data_dir is not None and not demo else None
        if self.alternate_data is not None:
            self.root.title(self.root.title()+'（別データ）')
        self.root.geometry('1080x760')
        self.root.minsize(860,600)
        self.root.configure(bg='#eef2f5')
        self.jobs=queue.Queue()
        self.events=queue.Queue()
        self.result_callbacks={}
        self.busy=True
        self.closing=False
        self.service=None
        self.models=[]
        self.startup_choice_pending=True
        self.controls=[]
        self.last_answer=None
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
        menu=tk.Menu(self.root)
        self.data_menu=tk.Menu(menu,tearoff=False)
        self.data_menu.add_command(label='記憶・計画のバックアップを保存…',command=self.backup)
        self.data_menu.add_command(label='バックアップを確認・別フォルダーに復元…',command=self.restore_dialog)
        self.data_menu.add_command(label='選択中の会話モデルを起動設定に保存',command=self.save_model_setting)
        menu.add_cascade(label='データ',menu=self.data_menu)
        self.root.configure(menu=menu)
        style=ttk.Style()
        style.theme_use('clam')
        style.configure('TButton',font=('Yu Gothic UI',10),padding=8)
        style.configure('TCombobox',font=('Yu Gothic UI',10),padding=5)
        style.configure('TCheckbutton',background='#eef2f5',font=('Yu Gothic UI',10))
        side=tk.Frame(self.root,bg='#152936',width=200)
        side.pack(side='left',fill='y')
        side.pack_propagate(False)
        tk.Label(side,text='TOMERIS',fg='#f4f8fa',bg='#152936',font=('Segoe UI',23,'bold')).pack(anchor='w',padx=22,pady=(26,0))
        tk.Label(side,text='思考を、次の行動へ。',fg='#a8c4ce',bg='#152936',font=('Yu Gothic UI',10)).pack(anchor='w',padx=22,pady=(4,16))
        buttons=[('計画を作る','plan'),('今日の計画','today'),('計画の履歴','plan_history'),('記憶を確認','memories'),('会話履歴','history'),('比較の記録','comparisons'),('PC情報','pc'),('基本人格','persona')]
        for label,kind in buttons:
            button=tk.Button(side,text=label,command=lambda k=kind:self.view(k),bg='#223c4b',fg='#ffffff',activebackground='#355568',activeforeground='white',relief='flat',anchor='w',padx=16,pady=5,font=('Yu Gothic UI',11))
            button.pack(fill='x',padx=14,pady=3)
            self.controls.append(button)
        button=ttk.Button(side,text='＋ 長期記憶を追加',command=self.remember)
        button.pack(fill='x',padx=14,pady=(12,4))
        self.controls.append(button)
        tk.Label(side,text='v0.23  •  Ollama\n会話はこのPCに保存',fg='#a8c4ce',bg='#152936',font=('Yu Gothic UI',10),justify='left').pack(side='bottom',anchor='w',padx=22,pady=24)
        main=tk.Frame(self.root,bg='#eef2f5')
        main.pack(side='left',fill='both',expand=True,padx=24,pady=20)
        header=tk.Frame(main,bg='#eef2f5'); header.pack(fill='x')
        tk.Label(header,text='トメリスと話す',bg='#eef2f5',fg='#172d3a',font=('Yu Gothic UI',22,'bold')).pack(side='left')
        refresh=ttk.Button(header,text='接続を確認',command=self.refresh)
        refresh.pack(side='right'); self.controls.append(refresh)
        google=ttk.Button(header,text='Googleカレンダー',command=self.open_google)
        google.pack(side='right',padx=8); self.controls.append(google)
        tk.Label(main,textvariable=self.connection,bg='#eef2f5',fg='#48626f',font=('Yu Gothic UI',10)).pack(anchor='w',pady=(4,14))
        options=tk.Frame(main,bg='#eef2f5'); options.pack(fill='x',pady=(0,12))
        self.mode_box=ttk.Combobox(options,textvariable=self.mode,values=['会話','会話＋自動検索','ネット検索','2モデル比較'],state='readonly',width=13)
        self.mode_box.pack(side='left',padx=(0,8)); self.mode_box.bind('<<ComboboxSelected>>',lambda e:self.control_state())
        self.model_box=ttk.Combobox(options,textvariable=self.model,state='readonly',width=22)
        self.model_box.pack(side='left',padx=(0,8))
        self.second_box=ttk.Combobox(options,textvariable=self.second_model,state='disabled',width=22)
        self.second_box.pack(side='left')
        copy_bar=tk.Frame(main,bg='#eef2f5'); copy_bar.pack(fill='x',pady=(0,6))
        self.copy_button=ttk.Button(copy_bar,text='最後の回答をコピー',command=self.copy_answer,state='disabled')
        self.copy_button.pack(side='right')
        self.transcript=ScrolledText(main,wrap='word',font=('Yu Gothic UI',11),bg='#ffffff',fg='#243b47',relief='flat',padx=18,pady=16,state='disabled',height=15)
        self.transcript.pack(fill='both',expand=True)
        self.transcript.tag_configure('you',foreground='#087f83',font=('Yu Gothic UI',11,'bold'),spacing1=15)
        self.transcript.tag_configure('assistant',foreground='#172d3a',font=('Yu Gothic UI',11,'bold'),spacing1=15)
        self.transcript.tag_configure('notice',foreground='#657887',font=('Yu Gothic UI',10),spacing1=10)
        self.transcript.tag_configure('body',spacing3=12)
        self.append('トメリス','こんにちは。質問や相談を入力してください。左のボタンから記憶やPC情報も確認できます。')
        self.last_answer=None
        self.copy_button.configure(state='disabled')
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
    def open_source(self,url):
        if self.closing or not public_url(url): return
        try:
            if not webbrowser.open(url): self.status.set('ブラウザーを開けませんでした。URLをコピーして開いてください。')
        except Exception:
            self.status.set('ブラウザーを開けませんでした。URLをコピーして開いてください。')
    def copy_answer(self):
        if self.closing or self.busy or not self.last_answer: return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.last_answer)
        except tk.TclError:
            self.status.set('コピーできませんでした。もう一度お試しください。')
            return
        self.status.set('最後の回答をコピーしました。メモ帳などに貼り付けられます。')
    def append(self,title,text):
        if title=='トメリス' and text.strip():
            self.last_answer=text
            self.copy_button.configure(state='normal' if not self.busy and not self.closing else 'disabled')
        self.transcript.configure(state='normal')
        tag='you' if title=='あなた' else ('notice' if title=='お知らせ' else 'assistant')
        self.transcript.insert('end',title+'\n',tag)
        body_start=self.transcript.index('end-1c')
        self.transcript.insert('end',text+'\n\n','body')
        for match in re.finditer(r'https?://[^\s<>]+',text):
            url=match.group(0)
            if not public_url(url): continue
            tag='url_'+str(len(self.transcript.tag_names()))
            self.transcript.tag_add(tag,f'{body_start}+{match.start()}c',f'{body_start}+{match.end()}c')
            self.transcript.tag_configure(tag,foreground='#006aaa',underline=True)
            self.transcript.tag_bind(tag,'<Button-1>',lambda event,u=url:self.open_source(u))
        self.transcript.configure(state='disabled')
        self.transcript.see('end')
    def control_state(self):
        active=not self.busy and not self.closing and self.service is not None
        self.copy_button.configure(state='normal' if active and self.last_answer else 'disabled')
        for index in (0,1):
            self.data_menu.entryconfigure(index,state='normal' if active else 'disabled')
        self.data_menu.entryconfigure(2,state='normal' if active and self.model.get() in self.models else 'disabled')
        for control in self.controls:
            control.configure(state='normal' if active else 'disabled')
        for control in (self.mode_box,self.model_box):
            control.configure(state='readonly' if active else 'disabled')
        self.second_box.configure(state='readonly' if active and self.mode.get()=='2モデル比較' else 'disabled')
        self.memory_check.configure(state='normal' if active and self.mode.get()!='ネット検索' else 'disabled')
        if self.mode.get() in ('会話＋自動検索','ネット検索') and not self.busy:
            self.status.set('検索時は今回の質問をBingへ送ります。記憶・過去会話は送りません。')
        dialog=getattr(self,'plan_window',None)
        if dialog is not None and dialog.winfo_exists():
            for control in self.plan_controls:
                control.configure(state='normal' if active else 'disabled')
        panel=getattr(self,'google_panel',None)
        if panel is not None:
            panel.state()
        panel=getattr(self,'today_panel',None)
        if panel is not None:
            panel.state()
        panel=getattr(self,'plan_history_panel',None)
        if panel is not None:
            panel.state()
        panel=getattr(self,'reflection_panel',None)
        if panel is not None:
            panel.state()
        panel=getattr(self,'weekly_panel',None)
        if panel is not None:
            panel.state()
        panel=getattr(self,'restore_panel',None)
        if panel is not None:
            panel.state()
        panel=getattr(self,'memory_panel',None)
        if panel is not None: panel.state()
        panel=getattr(self,'conversation_panel',None)
        if panel is not None:
            panel.state()
    def save_model_setting(self):
        if self.busy or self.closing: return
        model=self.model.get()
        self.submit('reply',lambda:self.service.save_startup_model(model),'起動時のモデル設定を保存しています…')
    def restore_dialog(self):
        if self.busy or self.closing: return
        path=filedialog.askopenfilename(parent=self.root,title='トメリスのバックアップZIPを選ぶ',filetypes=[('ZIPファイル','*.zip')])
        if path:
            self.restore_panel=RestorePanel(self,path)
    def backup(self):
        if self.busy or self.closing: return
        path=filedialog.asksaveasfilename(parent=self.root,title='記憶・計画のバックアップ（個人の記録を含むZIP）',
            confirmoverwrite=False,defaultextension='.zip',initialfile='tomeris_backup_'+datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d_%H%M%S')+'.zip',
            filetypes=[('ZIPファイル','*.zip')])
        if path:
            self.submit('reply',lambda:self.service.export_backup(path),'バックアップを作成・確認しています…')
    def open_google(self):
        if self.busy or self.closing:
            return
        if self.service.demo:
            messagebox.showinfo('画面確認用','Google接続は通常起動で利用してください。',parent=self.root); return
        self.google_panel=GooglePanel(self)
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
        elif self.mode.get() in ('会話＋自動検索','ネット検索'):
            automatic=self.mode.get()=='会話＋自動検索'
            func=lambda:self.service.web_chat(question,model,use_memory,automatic,lambda s:self.events.put(('progress',s)))
            label='検索の必要性を確認しています…'
        else:
            func=lambda:self.service.chat(question,model,use_memory)
            label='回答を準備しています…'
        if self.submit('reply',func,label):
            self.append('あなた',question)
            self.entry.delete('1.0','end')
        return 'break'
    def view(self,kind):
        if kind=='memories':
            if not self.busy and not self.closing:
                self.memory_panel=MemoryPanel(self)
            return
        if kind=='history':
            if not self.busy and not self.closing:
                self.conversation_panel=ConversationPanel(self)
            return
        if kind=='plan_history':
            if not self.busy and not self.closing:
                self.plan_history_panel=PlanHistoryPanel(self)
            return
        if kind=='today':
            if not self.busy and not self.closing:
                self.today_panel=TodayPanel(self)
            return
        if kind=='plan':
            self.plan_dialog(); return
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
    def plan_dialog(self,initial=None):
        if self.busy or self.closing:
            return
        dialog=tk.Toplevel(self.root)
        self.plan_window=dialog
        dialog.title('今日の計画を作る')
        dialog.geometry('680x620'); dialog.minsize(620,600)
        dialog.transient(self.root); dialog.grab_set()
        day=today()
        ttk.Label(dialog,text=f'{day}（日本時間） / 提案を確認・修正してから保存します。').pack(anchor='w',padx=18,pady=12)
        ttk.Label(dialog,text='今日やりたいこと').pack(anchor='w',padx=18)
        goal=tk.Text(dialog,height=3,wrap='word',font=('Yu Gothic UI',11))
        goal.pack(fill='x',padx=18,pady=6)
        budget_row=ttk.Frame(dialog); budget_row.pack(fill='x',padx=18,pady=6)
        ttk.Label(budget_row,text='使える時間（分）').pack(side='left')
        budget=tk.StringVar(value='30')
        budget_entry=ttk.Spinbox(budget_row,from_=1,to=1440,textvariable=budget,width=8)
        budget_entry.pack(side='left',padx=8)
        notice=tk.StringVar(value='手入力でも作れます。空欄の行動は保存しません。')
        ttk.Label(dialog,textvariable=notice,wraplength=590).pack(anchor='w',padx=18,pady=8)
        rows=[]; row_controls=[]
        for i in range(3):
            row=ttk.Frame(dialog); row.pack(fill='x',padx=18,pady=7)
            ttk.Label(row,text=f'{i+1}.').pack(side='left')
            title=tk.StringVar(); minutes=tk.StringVar(value='10')
            entry=ttk.Entry(row,textvariable=title); entry.pack(side='left',fill='x',expand=True,padx=6)
            duration=ttk.Entry(row,textvariable=minutes,width=5); duration.pack(side='left')
            ttk.Label(row,text=' 分').pack(side='left')
            rows.append((title,minutes)); row_controls.extend([entry,duration])
        if initial is not None:
            dialog.title('今日の計画・引き継ぎ下書き（未保存）')
            goal.insert('1.0',initial['goal'])
            budget.set(str(initial['budget']))
            for i,task in enumerate(initial['tasks']):
                rows[i][0].set(task['title']); rows[i][1].set(str(task['minutes']))
            notice.set(initial['notice'])
        def inputs():
            try:
                available=int(budget.get())
            except ValueError:
                raise ValueError('使える時間を整数で入力してください。')
            text=goal.get('1.0','end-1c').strip()
            validate(text,available,[{'title':'確認','minutes':1}])
            return text,available
        def invoke(operation,callback,label):
            def run():
                try:
                    result=(None,operation())
                except Exception as exc:
                    result=(str(exc),None)
                return callback,result
            self.submit('plan_result',run,label)
            notice.set(label)
        def drafted(result):
            if not dialog.winfo_exists():
                return
            error,plan=result
            if error:
                notice.set(error); return
            for i,(title,minutes) in enumerate(rows):
                task=plan['tasks'][i] if i<len(plan['tasks']) else {'title':'','minutes':10}
                title.set(task['title']); minutes.set(str(task['minutes']))
            notice.set('AIの提案です。内容と時間を確認・修正し「この内容を保存」を押してください。')
        def propose():
            try:
                text,available=inputs()
            except ValueError as exc:
                notice.set(str(exc)); return
            if any(title.get().strip() for title,_ in rows):
                if not messagebox.askyesno('提案で置き換える','入力中の行動をAIの提案で置き換えますか？',parent=dialog):
                    return
            model=self.model.get()
            invoke(lambda:self.service.draft_plan(text,available,model),drafted,'ローカルAIが計画を提案しています…')
        def saved(result):
            error,text=result
            if error:
                if dialog.winfo_exists():
                    notice.set(error)
                else:
                    self.append('お知らせ',error)
                return
            if dialog.winfo_exists():
                dialog.destroy()
            self.append('トメリス',text)
        def save():
            try:
                text,available=inputs()
                tasks=[{'title':title.get(),'minutes':int(minutes.get())} for title,minutes in rows if title.get().strip()]
                plan=validate(text,available,tasks)
            except ValueError as exc:
                notice.set(str(exc)); return
            invoke(lambda:self.service.save_plan(plan['goal'],plan['budget'],plan['tasks'],day),saved,'確認した計画を保存しています…')
        actions=ttk.Frame(dialog); actions.pack(fill='x',padx=18,pady=16)
        propose_button=ttk.Button(actions,text='AIに提案してもらう',command=propose)
        propose_button.pack(side='left')
        save_button=ttk.Button(actions,text='この内容を保存',command=save)
        save_button.pack(side='right')
        self.plan_controls=[goal,budget_entry,propose_button,save_button]+row_controls
        def dismiss():
            if self.busy:
                notice.set('処理が終わるまでお待ちください。'); return
            dialog.destroy()
        dialog.protocol('WM_DELETE_WINDOW',dismiss)
        goal.focus_set()

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
                if kind=='plan_result':
                    callback,result=value
                    token=object()
                    self.result_callbacks[token]=callback
                    value=(token,result)
                    callback=None
                func=None; job=None
                self.events.put((kind,value))
            except Exception as exc:
                self.events.put(('error',(kind,str(exc))))
    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='ready':
                    self.service=value; self.busy=False
                    if self.alternate_data is not None:
                        self.append('お知らせ','別データで起動しています。保存先：'+str(self.alternate_data))
                    if value.settings_notice:
                        self.append('お知らせ',value.settings_notice)
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
                        if self.startup_choice_pending and value:
                            selected,notice=choose_startup_model(self.service.startup_model,value,self.model.get())
                            self.model.set(selected); self.startup_choice_pending=False
                            if notice: self.append('お知らせ',notice)
                        if value and self.model.get() not in value:
                            self.model.set(value[0])
                        if len(value)>1 and (self.second_model.get() not in value or self.second_model.get()==self.model.get()):
                            self.second_model.set(next(m for m in value if m!=self.model.get()))
                        self.connection.set(f'ローカルAI・{len(value)}モデル確認済み' if value else 'モデル未導入・記憶とPC情報は利用できます')
                    elif kind=='plan_result':
                        token,result=value
                        callback=self.result_callbacks.pop(token)
                        callback(result)
                        callback=None
                    elif kind=='error':
                        failed,error=value
                        if failed=='models':
                            self.connection.set('Ollamaに接続できません・記憶とPC情報は利用できます')
                        self.append('お知らせ',error)
                    else:
                        self.append('トメリス',value)
                    if not self.closing:
                        self.status.set('準備できました')
                        google_open=getattr(self,'google_panel',None) and self.google_panel.window.winfo_exists()
                        today_open=getattr(self,'today_panel',None) and self.today_panel.window.winfo_exists()
                        history_open=getattr(self,'plan_history_panel',None) and self.plan_history_panel.window.winfo_exists()
                        restore_open=getattr(self,'restore_panel',None) and self.restore_panel.window.winfo_exists()
                        conversation_open=getattr(self,'conversation_panel',None) and self.conversation_panel.window.winfo_exists()
                        memory_open=getattr(self,'memory_panel',None) and self.memory_panel.window.winfo_exists()
                        if not memory_open and not conversation_open and not restore_open and not history_open and not today_open and not google_open and not (getattr(self,'plan_window',None) and self.plan_window.winfo_exists()):
                            self.entry.focus_set()
                self.control_state()
        except queue.Empty:
            pass
        self.root.after(80,self.poll)
    def close(self):
        if self.closing:
            return
        self.closing=True
        if self.service is not None:
            self.service.google.cancel.set()
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
