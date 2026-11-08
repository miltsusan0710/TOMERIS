"""Date filter, saved plan revisions and full text history."""
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tomeris_plan_reflection import describe
from tomeris_reflection_ui import ReflectionPanel

class PlanHistoryPanel:
    def __init__(self,app):
        self.app=app; self.rows=[]; self.visible=[]
        self.window=tk.Toplevel(app.root); self.window.title('計画の履歴')
        self.window.geometry('800x650'); self.window.minsize(600,500)
        self.window.transient(app.root); self.window.grab_set()
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.columnconfigure(0,weight=1)
        self.window.rowconfigure(3,weight=1)
        ttk.Label(self.window,text='計画の履歴',font=('Yu Gothic UI',18,'bold')).grid(row=0,column=0,sticky='w',padx=20,pady=(18,8))
        bar=ttk.Frame(self.window); bar.grid(row=1,column=0,sticky='ew',padx=20,pady=6)
        ttk.Label(bar,text='日付：').pack(side='left')
        self.date_box=ttk.Combobox(bar,state='readonly',width=20,values=['すべての日付'])
        self.date_box.current(0); self.date_box.pack(side='left')
        self.date_box.bind('<<ComboboxSelected>>',lambda e:self.filter())
        self.reload=ttk.Button(bar,text='読み直す',command=self.load); self.reload.pack(side='right')
        list_frame=ttk.Frame(self.window); list_frame.grid(row=2,column=0,sticky='ew',padx=20,pady=8)
        self.list=tk.Listbox(list_frame,height=3,width=1,exportselection=False,font=('Yu Gothic UI',10))
        self.list.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(list_frame,orient='vertical',command=self.list.yview); scroll.pack(side='right',fill='y')
        self.list.configure(yscrollcommand=scroll.set); self.list.bind('<<ListboxSelect>>',lambda e:self.select())
        self.detail=ScrolledText(self.window,wrap='word',height=1,width=1,state='disabled',font=('Yu Gothic UI',11))
        self.detail.grid(row=3,column=0,sticky='nsew',padx=20,pady=8)
        self.message=tk.StringVar(value='履歴を読み込んでいます…')
        ttk.Label(self.window,textvariable=self.message,wraplength=520).grid(row=4,column=0,sticky='ew',padx=20,pady=6)
        footer=ttk.Frame(self.window); footer.grid(row=5,column=0,sticky='ew',padx=20,pady=(0,16))
        self.carry_button=ttk.Button(footer,text='残った行動を今日の下書きに',command=self.carry)
        self.carry_button.grid(row=1,column=0,sticky='w',pady=(6,0))
        footer.columnconfigure(0,weight=1)
        self.reflect_button=ttk.Button(footer,text='この計画の振り返りを書く',command=self.reflect)
        self.reflect_button.grid(row=0,column=0,sticky='w')
        self.exit_button=ttk.Button(footer,text='閉じる',command=self.close); self.exit_button.grid(row=1,column=1,sticky='e',pady=(6,0))
        self.load(); self.state()
    def state(self):
        if not self.window.winfo_exists():
            return
        active=not self.app.busy and not self.app.closing
        for item in [self.reload,self.exit_button,self.list,self.carry_button,self.reflect_button]:
            item.configure(state='normal' if active else 'disabled')
        self.date_box.configure(state='readonly' if active else 'disabled')
    def text(self,value):
        self.detail.configure(state='normal'); self.detail.delete('1.0','end'); self.detail.insert('end',value); self.detail.configure(state='disabled')
    def load(self):
        if self.app.busy or self.app.closing:
            return
        def work():
            try:
                result=(None,self.app.service.plan_history())
            except (ValueError,OSError) as exc:
                result=(str(exc),None)
            except Exception:
                result=('履歴を読み取れませんでした。',None)
            return loaded,result
        def loaded(result):
            if not self.window.winfo_exists():
                return
            error,rows=result
            self.state()
            if error:
                self.message.set('読込失敗：'+error)
                self.rows=[]; self.visible=[]; self.list.delete(0,'end'); self.text('履歴を取得できませんでした。')
                return
            chosen=self.date_box.get()
            self.rows=rows
            dates=['すべての日付']+sorted({row['plan']['date'] for row in rows},reverse=True)
            self.date_box.configure(values=dates)
            self.date_box.set(chosen if chosen in dates else dates[0])
            self.filter()
        if self.app.submit('plan_result',work,'計画の履歴を読み込んでいます…'):
            self.message.set('履歴を読み込んでいます…'); self.state()
    def filter(self):
        chosen=self.date_box.get()
        self.visible=[row for row in self.rows if chosen=='すべての日付' or row['plan']['date']==chosen]
        self.list.delete(0,'end')
        for row in self.visible:
            plan=row['plan']; goal=plan['goal'].replace('\n',' ')
            if len(goal)>32:
                goal=goal[:32]+'…'
            latest='最新' if row['latest'] else '以前'
            self.list.insert('end',f"{plan['date']} / {row['revision']}件目（{latest}）  {goal}")
        self.message.set(f'{len(self.visible)}件。新しい順に表示しています。計画を選んでください。')
        if self.visible:
            self.list.selection_set(0); self.select()
        else:
            self.text('保存された計画はまだありません。「計画を作る」から作成してください。')
    def select(self):
        selected=self.list.curselection()
        if selected and selected[0]<len(self.visible):
            self.text(describe(self.visible[selected[0]]).replace('この画面は閲覧専用です。チェックの変更は「今日の計画」で行ってください。','元の計画は変更しません。下書きを作った後、確認して保存できます。'))
    def reflect(self):
        if self.app.busy or self.app.closing: return
        selected=self.list.curselection()
        if not selected or selected[0]>=len(self.visible):
            self.message.set('振り返る計画を一覧から選んでください。'); return
        self.app.reflection_panel=ReflectionPanel(self,self.visible[selected[0]]['id'])
    def carry(self):
        if self.app.busy or self.app.closing:
            return
        selected=self.list.curselection()
        if not selected or selected[0]>=len(self.visible):
            self.message.set('引き継ぎ元の計画を一覧から選んでください。'); return
        identifier=self.visible[selected[0]]['id']
        def work():
            try:
                result=(None,self.app.service.carry_draft(identifier))
            except (ValueError,OSError) as exc:
                result=(str(exc),None)
            except Exception:
                result=('下書きを準備できませんでした。',None)
            return prepared,result
        def prepared(result):
            if not self.window.winfo_exists():
                return
            error,draft=result
            if error:
                self.message.set(error); self.state(); return
            self.window.destroy()
            self.app.plan_dialog(initial=draft)
        if self.app.submit('plan_result',work,'引き継ぐ行動を確認しています…'):
            self.message.set('引き継ぐ行動を確認しています…'); self.state()
    def close(self):
        if self.app.busy:
            self.message.set('読込が終わるまでお待ちください。'); return
        self.window.destroy()
