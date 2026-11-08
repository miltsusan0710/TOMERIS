"""Date filter, saved plan revisions and full text history."""
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tomeris_plan_history import describe

class PlanHistoryPanel:
    def __init__(self,app):
        self.app=app; self.rows=[]; self.visible=[]
        self.window=tk.Toplevel(app.root); self.window.title('計画の履歴')
        self.window.geometry('800x650'); self.window.minsize(600,500)
        self.window.transient(app.root); self.window.grab_set()
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        ttk.Label(self.window,text='計画の履歴',font=('Yu Gothic UI',18,'bold')).pack(anchor='w',padx=20,pady=(18,8))
        bar=ttk.Frame(self.window); bar.pack(fill='x',padx=20,pady=6)
        ttk.Label(bar,text='日付：').pack(side='left')
        self.date_box=ttk.Combobox(bar,state='readonly',width=20,values=['すべての日付'])
        self.date_box.current(0); self.date_box.pack(side='left')
        self.date_box.bind('<<ComboboxSelected>>',lambda e:self.filter())
        self.reload=ttk.Button(bar,text='読み直す',command=self.load); self.reload.pack(side='right')
        list_frame=ttk.Frame(self.window); list_frame.pack(fill='x',padx=20,pady=8)
        self.list=tk.Listbox(list_frame,height=5,exportselection=False,font=('Yu Gothic UI',10))
        self.list.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(list_frame,orient='vertical',command=self.list.yview); scroll.pack(side='right',fill='y')
        self.list.configure(yscrollcommand=scroll.set); self.list.bind('<<ListboxSelect>>',lambda e:self.select())
        self.detail=ScrolledText(self.window,wrap='word',state='disabled',font=('Yu Gothic UI',11))
        self.detail.pack(fill='both',expand=True,padx=20,pady=8)
        self.message=tk.StringVar(value='履歴を読み込んでいます…')
        ttk.Label(self.window,textvariable=self.message,wraplength=730).pack(anchor='w',padx=20,pady=6)
        self.exit_button=ttk.Button(self.window,text='閉じる',command=self.close); self.exit_button.pack(anchor='e',padx=20,pady=(0,16))
        self.load(); self.state()
    def state(self):
        if not self.window.winfo_exists():
            return
        active=not self.app.busy and not self.app.closing
        for item in [self.reload,self.exit_button,self.list]:
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
        self.message.set(f'{len(self.visible)}件の計画。日付と保存順で新しいものから表示しています。閲覧では記録を変更しません。')
        if self.visible:
            self.list.selection_set(0); self.select()
        else:
            self.text('保存された計画はまだありません。「計画を作る」から作成してください。')
    def select(self):
        selected=self.list.curselection()
        if selected and selected[0]<len(self.visible):
            self.text(describe(self.visible[selected[0]]))
    def close(self):
        if self.app.busy:
            self.message.set('読込が終わるまでお待ちください。'); return
        self.window.destroy()
