"""TOMERIS desktop v0.78. Tk UI with a single serialized background worker."""
import argparse
from tomeris_hud_orb import Orb
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
from tomeris_adaptive_collection import DesktopService as PlanService
from tomeris_methods_ui import MethodsPanel
from tomeris_sources_ui_v056 import SourcesPanel
from tomeris_collection_ui_v078 import CollectionPanel
from tomeris_research_history_ui import ResearchHistoryPanel
from tomeris_memory_restore_ui import MemoryPanel
from tomeris_history_search_ui import ConversationPanel
from tomeris_restore_ui_v034 import RestorePanel
from tomeris_tomorrow_ui import PlanHistoryPanel
from tomeris_today_ui import TodayPanel
from tomeris_google import GoogleCalendar
from tomeris_google_ui import GooglePanel

from tomeris_restore_v063 import DesktopService as BackupService
from tomeris_restore_v063 import DesktopService as RestoreService

class DesktopService(PlanService):
    export_backup=BackupService.export_backup
    inspect_backup=RestoreService.inspect_backup
    restore_backup=RestoreService.restore_backup
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.google=GoogleCalendar(self.data_dir)


class TomerisWindow:
    def __init__(self,root,data_dir=None,demo=False):
        self.root=root
        self.root.title('トメリス | Windowsアプリ v0.78'+('（画面確認用）' if demo else ''))
        self.alternate_data=Path(data_dir).resolve() if data_dir is not None and not demo else None
        if self.alternate_data is not None:
            self.root.title(self.root.title()+'（別データ）')
        self.root.geometry('1280x850')
        self.root.minsize(880,760)
        self.root.configure(bg='#08131f')
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
        self.mode=tk.StringVar(value='会話＋自動検索')
        self.use_memory=tk.BooleanVar(value=False)
        self.status=tk.StringVar(value='記憶を準備しています…')
        self.connection=tk.StringVar(value='ローカルAI・接続確認前')
        self.show_sidebar=tk.BooleanVar(value=True)
        self.show_chat_settings=tk.BooleanVar(value=False)
        self.large_input=False
        self.make_ui()
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.root.after(80,self.poll)
        threading.Thread(target=self.worker,args=(data_dir,demo),daemon=True).start()
    def make_ui(self):
        menu=tk.Menu(self.root)
        self.data_menu=tk.Menu(menu,tearoff=False)
        self.data_menu.add_command(label='記憶・計画・資料のバックアップを保存…',command=self.backup)
        self.data_menu.add_command(label='バックアップを確認・別フォルダーに復元…',command=self.restore_dialog)
        self.data_menu.add_command(label='選択中の会話モデルを起動設定に保存',command=self.save_model_setting)
        menu.add_cascade(label='データ',menu=self.data_menu)
        menu.add_command(label='調査方法・Google検索',command=self.open_methods)
        view_menu=tk.Menu(menu,tearoff=False)
        view_menu.add_checkbutton(label='左メニューを表示',variable=self.show_sidebar,command=self.update_chat_layout)
        view_menu.add_checkbutton(label='会話設定を表示',variable=self.show_chat_settings,command=self.update_chat_layout)
        menu.add_cascade(label='表示',menu=view_menu)
        learning_menu=tk.Menu(menu,tearoff=False)
        learning_menu.add_command(label='保存資料を検索・管理…',command=self.open_sources)
        for label,command in [('学習した資料を見る','学習した資料を見せて'),('資料学習を停止','ネット学習を停止'),('資料学習を再開','ネット学習を再開'),('保存した資料を消去','学習した資料を消去')]:
            learning_menu.add_command(label=label,command=lambda q=command:self.learning_action(q))
        learning_menu.add_command(label='調査履歴を見る・再調査',command=self.open_research_history)
        learning_menu.add_command(label='自動収集の状態',command=lambda:self.auto_source_action('自動資料収集の状態'))
        learning_menu.add_command(label='自動収集を停止',command=lambda:self.auto_source_action('自動資料収集を停止'))
        learning_menu.add_command(label='自動収集を再開',command=lambda:self.auto_source_action('自動資料収集を再開'))
        learning_menu.add_command(label='自動収集のテーマ・結果',command=self.open_collection)
        learning_menu.add_command(label='調査を比較・採点（実験）',command=self.open_trial)
        learning_menu.add_command(label='採点済み資料を学習用・評価用に分ける',command=self.open_dataset)
        from tomeris_experiment_view import open_experiment
        learning_menu.add_command(label='データセットで学習実験（通常回答には未適用）',command=lambda:open_experiment(self))
        from tomeris_trial_coverage_ui import open_coverage
        learning_menu.add_command(label='比較試行の成功・失敗を見る',command=lambda:open_coverage(self))
        from tomeris_trial_backup_ui import open_backup
        learning_menu.add_command(label='比較記録・採点をバックアップ…',command=lambda:open_backup(self))
        learning_menu.add_command(label='比較記録バックアップを検査…',command=lambda:open_backup(self,check=True))
        menu.add_cascade(label='資料学習',menu=learning_menu)
        menu.add_command(label='使い方',command=lambda:messagebox.showinfo('トメリスの使い方','普段の相談はそのまま入力してください。\n天気：今日の天気は？ → 平塚市\n計算：計算: (1200 + 800) * 1.1\n情報収集：調査: Ollama\n\nEnterで改行、Ctrl+Enterで送信。\n文字サイズは会話欄上の「小」「大」で変更できます。「表示」メニューで左メニューや会話設定を表示できます。\n\n調査方法は上部の「調査方法・Google検索」で選べます。初期設定は自動選択です。「Googleで」「Wikipediaで」などの指定を優先します。天気はOpen-Meteoを利用します。\n保存済みの記憶は検索先へ送りません。',parent=self.root))
        from tomeris_multimodal_ui_v071 import attach_menu
        self.media_actions=attach_menu(self,menu)
        self.root.configure(menu=menu,bg='#08131f')
        style=ttk.Style();style.theme_use('clam')
        self.root.option_add('*TCombobox*Listbox.background','#102536')
        self.root.option_add('*TCombobox*Listbox.foreground','#e1eef5')
        self.root.option_add('*TCombobox*Listbox.selectBackground','#28617a')
        self.root.option_add('*TCombobox*Listbox.selectForeground','#ffffff')
        style.configure('TButton',font=('Yu Gothic UI',10),padding=(10,6),background='#102536',foreground='#dceff6',bordercolor='#295265',lightcolor='#102536',darkcolor='#295265')
        style.configure('TButton',borderwidth=1,relief='flat')
        style.map('TCombobox',fieldbackground=[('readonly','#102536'),('disabled','#10202d')],background=[('readonly','#183647')])
        style.map('TButton',background=[('active','#204b60')],foreground=[('disabled','#718b9d')])
        style.configure('TCombobox',font=('Yu Gothic UI',10),padding=5,fieldbackground='#102536',background='#183647',foreground='#dceff6')
        style.configure('TCheckbutton',background='#08131f',foreground='#b4ccd8',font=('Yu Gothic UI',10))
        self.root.columnconfigure(1,weight=1);self.root.rowconfigure(0,weight=1)
        side=tk.Frame(self.root,bg='#0c1c2b',width=210,highlightbackground='#214655',highlightthickness=1)
        self.sidebar=side
        side.grid(row=0,column=0,sticky='ns');side.grid_propagate(False)
        side.columnconfigure(0,weight=1);side.rowconfigure(10,weight=1)
        tk.Label(side,text='トメリス',bg='#0c1c2b',fg='#67e5f5',font=('Segoe UI',17,'bold')).grid(row=0,column=0,sticky='w',padx=18,pady=(22,4))
        tk.Label(side,text='パーソナルAIアシスタント',bg='#0c1c2b',fg='#9ab5c7',font=('Yu Gothic UI',9)).grid(row=1,column=0,sticky='w',padx=18,pady=(0,18))
        buttons=[('＋ タスクを計画','plan'),('今日のスケジュール','today'),('計画の履歴','plan_history'),('記憶を確認','memories'),('会話の履歴','history'),('回答を比較','comparisons'),('PC情報','pc'),('基本人格','persona')]
        for row,(label,kind) in enumerate(buttons,2):
            button=tk.Button(side,text=label,command=lambda k=kind:self.view(k),bg='#0c1c2b',fg='#c1dce8',activebackground='#173b4c',activeforeground='#9cf4ff',disabledforeground='#718b9d',relief='flat',anchor='w',padx=12,pady=5,font=('Yu Gothic UI',10),cursor='hand2')
            button.grid(row=row,column=0,sticky='ew',padx=10,pady=2);self.controls.append(button)
        style.configure('Side.TFrame',background='#0c1c2b')
        actions=ttk.Frame(side,style='Side.TFrame');actions.grid(row=11,column=0,sticky='ew',padx=12,pady=10)
        for label,command in [('＋ 長期記憶を追加',self.remember),('接続を確認',self.refresh),('資料を管理',self.open_sources),('会話設定',self.toggle_settings),('Googleカレンダー',self.open_google)]:
            button=ttk.Button(actions,text=label,command=command);button.pack(fill='x',pady=3);self.controls.append(button)
        tk.Label(side,text='v0.78  /  ローカルAI',bg='#0c1c2b',fg='#9ab5c7',font=('Yu Gothic UI',9)).grid(row=12,column=0,sticky='w',padx=18,pady=(4,16))
        main=tk.Frame(self.root,bg='#08131f');main.grid(row=0,column=1,sticky='nsew',padx=14,pady=8)
        main.columnconfigure(0,weight=1);main.rowconfigure(3,weight=1)
        self.orb=Orb(main,self,height=48);self.orb.grid(row=0,column=0,sticky='ew')
        self.connection_label=tk.Label(main,textvariable=self.connection,bg='#08131f',fg='#9ab5c7',font=('Yu Gothic UI',9),anchor='center')
        self.connection_label.grid(row=1,column=0,sticky='ew',pady=(0,4))
        options=tk.Frame(main,bg='#08131f');self.options_frame=options;options.grid(row=2,column=0,sticky='ew',pady=(0,6))
        for i in range(3):options.columnconfigure(i,weight=1,uniform='options')
        self.mode_box=ttk.Combobox(options,textvariable=self.mode,values=['会話','会話＋自動検索','ネット検索','情報収集','2モデル比較'],state='readonly',width=1)
        self.mode_box.grid(row=0,column=0,sticky='ew',padx=(0,8));self.mode_box.bind('<<ComboboxSelected>>',lambda e:self.control_state())
        self.model_box=ttk.Combobox(options,textvariable=self.model,state='readonly',width=1);self.model_box.grid(row=0,column=1,sticky='ew',padx=(0,8))
        self.second_box=ttk.Combobox(options,textvariable=self.second_model,state='disabled',width=1);self.second_box.grid(row=0,column=2,sticky='ew')
        options.grid_remove()
        card=tk.Frame(main,bg='#102536',highlightbackground='#295265',highlightthickness=1)
        card.grid(row=3,column=0,sticky='nsew');card.columnconfigure(0,weight=1);card.rowconfigure(1,weight=1)
        bar=tk.Frame(card,bg='#102536');bar.grid(row=0,column=0,sticky='ew',padx=12,pady=6)
        tk.Label(bar,text='会話',bg='#102536',fg='#67e5f5',font=('Yu Gothic UI',12,'bold')).pack(side='left')
        self.copy_button=ttk.Button(bar,text='回答コピー',command=self.copy_answer,state='disabled');self.copy_button.pack(side='right')
        ttk.Button(bar,text='大',width=3,command=lambda:self.change_text_size(1)).pack(side='right',padx=(2,8))
        ttk.Button(bar,text='小',width=3,command=lambda:self.change_text_size(-1)).pack(side='right')
        ttk.Button(bar,text='最新へ',command=lambda:self.transcript.see('end')).pack(side='right',padx=4)
        self.chat_size=13
        from tomeris_chat_cards_v069 import ChatCards
        self.transcript=ChatCards(card)
        self.transcript.vbar.configure(background='#183647',troughcolor='#102536',activebackground='#32778e')
        self.transcript.grid(row=1,column=0,sticky='nsew',padx=(4,0),pady=(0,8))
        self.append('トメリス','こんにちは。今日は何を一緒に考えましょう？\n質問や相談を下の入力欄に書いてください。')
        self.last_answer=None;self.copy_button.configure(state='disabled')
        compose=tk.Frame(main,bg='#08131f');compose.grid(row=4,column=0,sticky='ew',pady=(8,0));compose.columnconfigure(0,weight=1)
        self.memory_check=ttk.Checkbutton(compose,text='この質問で記憶を参照する',variable=self.use_memory);self.memory_check.grid(row=0,column=0,sticky='w',pady=(0,6))
        self.input_size_button=ttk.Button(compose,text='入力欄を広げる',command=self.toggle_input_size)
        self.input_size_button.grid(row=0,column=1,sticky='e',pady=(0,6))
        self.entry=tk.Text(compose,height=3,width=1,wrap='word',font=('Yu Gothic UI',12),bg='#102536',fg='#e1eef5',insertbackground='#51d5e9',relief='flat',highlightbackground='#295265',highlightcolor='#68edff',highlightthickness=1,padx=12,pady=10)
        self.entry.configure(selectbackground='#2c6177',selectforeground='#ffffff')
        self.entry.grid(row=2,column=0,sticky='ew');self.entry.bind('<Control-Return>',self.send)
        self.send_button=tk.Button(compose,text='送信  →',command=self.send,bg='#51d5e9',fg='#071923',activebackground='#8aedfa',activeforeground='#071923',disabledforeground='#456777',relief='flat',font=('Yu Gothic UI',11,'bold'),padx=20,pady=10,cursor='hand2')
        self.send_button.grid(row=2,column=1,sticky='ns',padx=(10,0));self.controls.append(self.send_button)
        quick=tk.Frame(compose,bg='#08131f');quick.grid(row=1,column=0,columnspan=2,sticky='w',pady=(0,8))
        for title,action in [('＋ 画像', 'image'),('● 音声入力','listen'),('♪ 読み上げ','speak'),('まとめて依頼','batch')]:
            button=ttk.Button(quick,text=title,command=self.media_actions[action]);button.pack(side='left',padx=(0,8));self.controls.append(button)
        self.audio_stop_button=ttk.Button(quick,text='■ 音声を停止',command=self.media_actions['stop'],state='disabled')
        self.audio_stop_button.pack(side='left',padx=(0,8))
        tk.Label(compose,text='Enterで改行  ·  Ctrl＋Enterで送信',bg='#08131f',fg='#9ab5c7',font=('Yu Gothic UI',9)).grid(row=3,column=0,sticky='w',pady=(5,0))
        self.status_label=tk.Label(main,textvariable=self.status,bg='#08131f',fg='#9ab5c7',font=('Yu Gothic UI',9),anchor='w',justify='left',wraplength=700)
        self.status_label.grid(row=5,column=0,sticky='ew',pady=(8,0))
        main.bind('<Configure>',self.fit_chat_layout)
        self.control_state()
        self.root.after(30000,self.auto_source_tick)
    def auto_source_action(self,text):
        if self.busy or self.closing or self.service is None:return
        self.submit('reply',lambda:self.service.chat(text,'unused'),'自動収集の設定を確認しています…')
    def auto_source_tick(self):
        if self.closing:return
        if self.service is not None and not self.busy and not self.entry.get('1.0','end').strip() and self.service.auto_sources_due():
            def work():return completed,self.service.collect_public_topic()
            def completed(result):
                if result:self.status.set(result)
            self.submit('plan_result',work,'公開資料を最大2テーマ確認しています…')
        self.root.after(30000,self.auto_source_tick)
    def open_sources(self):
        if self.busy or self.closing or self.service is None:return
        panel=getattr(self,'sources_panel',None)
        if panel is not None and panel.window.winfo_exists():panel.window.lift();return
        self.sources_panel=SourcesPanel(self)
    def learning_action(self,question):
        if self.busy or self.closing or self.service is None:return
        self.submit('reply',lambda:self.service.special(question),'資料学習の状態を確認しています…')
    def toggle_settings(self):
        self.show_chat_settings.set(not self.show_chat_settings.get())
        self.update_chat_layout()
    def update_chat_layout(self):
        if self.show_sidebar.get():self.sidebar.grid()
        else:self.sidebar.grid_remove()
        if self.show_chat_settings.get():self.options_frame.grid()
        else:self.options_frame.grid_remove()
    def toggle_input_size(self):
        self.large_input=not self.large_input
        self.entry.configure(height=4 if self.large_input else 2)
        self.input_size_button.configure(text='入力欄を縮める' if self.large_input else '入力欄を広げる')
    def fit_chat_layout(self,event):
        self.orb.configure(height=48)
        dense=float(self.root.tk.call('tk','scaling'))>2 and event.height<900
        if dense:self.connection_label.grid_remove()
        else:self.connection_label.grid()
        self.entry.configure(height=4 if self.large_input else 2)
        self.status_label.configure(wraplength=max(250,event.width-8))
    def change_text_size(self,delta):
        self.chat_size=max(10,min(18,self.chat_size+delta))
        self.transcript.set_font(self.chat_size)
        self.entry.configure(font=('Yu Gothic UI',self.chat_size))

    def open_methods(self):
        if self.busy or self.closing or self.service is None:return
        self.methods_panel=MethodsPanel(self)
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
        self.transcript.add(title,text,self.open_source)
    def open_research_history(self):
        if self.busy or self.closing:return
        panel=getattr(self,'research_history_panel',None)
        if panel and panel.window.winfo_exists():panel.window.lift();return
        self.research_history_panel=ResearchHistoryPanel(self)

    def open_dataset(self):
        if self.busy or self.closing or self.service is None:return
        panel=getattr(self,'dataset_panel',None)
        if panel and panel.window.winfo_exists():panel.window.lift();return
        from tomeris_trial_dataset_ui import DatasetPanel
        self.dataset_panel=DatasetPanel(self)

    def open_trial(self):
        if self.busy or self.closing or self.service is None:return
        panel=getattr(self,'trial_panel',None)
        if panel and panel.window.winfo_exists():panel.window.lift();return
        from tomeris_research_trials_ui import TrialPanel
        self.trial_panel=TrialPanel(self)

    def open_collection(self):
        if self.busy or self.closing:return
        panel=getattr(self,'collection_panel',None)
        if panel and panel.window.winfo_exists():panel.window.lift();return
        self.collection_panel=CollectionPanel(self)
    def control_state(self):
        if hasattr(self,'audio_stop_button'):
            self.audio_stop_button.configure(state='normal' if self.audio_active and not self.closing else 'disabled')
        panel=getattr(self,'collection_panel',None)
        if panel:panel.state()
        research_panel=getattr(self,"research_history_panel",None)
        if research_panel:research_panel.state()
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
        if self.mode.get()=='2モデル比較':
            self.second_box.grid();self.options_frame.columnconfigure(2,weight=1,uniform='options')
        else:
            self.second_box.grid_remove();self.options_frame.columnconfigure(2,weight=0,uniform='')
        self.memory_check.configure(state='normal' if active and self.mode.get() not in ('ネット検索','情報収集') else 'disabled')
        if self.mode.get() in ('会話＋自動検索','ネット検索','情報収集') and not self.busy:
            self.status.set('調査方法は自動選択します。方法を指定した質問では指定を優先します。検索語・指定URLを外部へ送ります。保存済みの記憶は送りません。')
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
        panel=getattr(self,'sources_panel',None)
        if panel is not None:panel.state()
        panel=getattr(self,'methods_panel',None)
        if panel is not None:panel.state()
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
        path=filedialog.asksaveasfilename(parent=self.root,title='記憶・計画・資料のバックアップ（個人の記録を含むZIP）',
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
        from tomeris_language_actions import action_for,perform
        action=action_for(question)
        if action and self.service is not None:
            self.append('あなた',question)
            self.entry.delete('1.0','end')
            perform(self,action)
            return 'break'
        model=self.model.get(); second=self.second_model.get(); use_memory=self.use_memory.get()
        if self.mode.get()=='2モデル比較':
            if model==second or model not in self.models or second not in self.models:
                messagebox.showinfo('比較するモデル','導入済みの異なる2モデルを選んでください。',parent=self.root)
                return 'break'
            query=('記憶を参照して：' if use_memory else '')+question
            func=lambda:self.service.compare(query,[model,second],lambda s:self.events.put(('progress',s)))
            label='2つのモデルを順に比較しています…'
        elif self.mode.get()=='情報収集':
            func=lambda:self.service.research(question,model,lambda s:self.events.put(('progress',s)))
            label='複数の検索語で情報を集めています…'
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
                        methods_open=getattr(self,'methods_panel',None) and self.methods_panel.window.winfo_exists()
                        sources_open=getattr(self,'sources_panel',None) and self.sources_panel.window.winfo_exists()
                        if not sources_open and not methods_open and not memory_open and not conversation_open and not restore_open and not history_open and not today_open and not google_open and not (getattr(self,'plan_window',None) and self.plan_window.winfo_exists()):
                            self.entry.focus_set()
                self.control_state()
        except queue.Empty:
            pass
        self.root.after(80,self.poll)
    def close(self):
        if self.closing:
            return
        self.closing=True
        self.audio_cancel.set()
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
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError,OSError):
        pass
    root=tk.Tk()
    TomerisWindow(root,args.data_dir,args.demo)
    root.mainloop()

if __name__=='__main__':
    main()
