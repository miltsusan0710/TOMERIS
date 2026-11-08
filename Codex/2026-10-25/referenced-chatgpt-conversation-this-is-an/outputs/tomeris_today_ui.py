"""Today's plan and persisted completion checkboxes."""
import tkinter as tk
from tkinter import ttk

class TodayPanel:
    def __init__(self,app):
        self.app=app; self.snapshot=None; self.checks=[]; self.variables=[]
        self.window=tk.Toplevel(app.root); self.window.title('今日の計画・完了チェック')
        self.window.geometry('700x650'); self.window.minsize(620,600)
        self.window.transient(app.root); self.window.grab_set()
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.heading=tk.StringVar(value='今日の計画を読み込んでいます…')
        ttk.Label(self.window,textvariable=self.heading,font=('Yu Gothic UI',15,'bold'),wraplength=590).pack(anchor='w',padx=20,pady=20)
        self.body=ttk.Frame(self.window); self.body.pack(fill='both',expand=True,padx=20)
        self.summary=tk.StringVar(); ttk.Label(self.window,textvariable=self.summary).pack(anchor='w',padx=20,pady=8)
        self.notice=tk.StringVar(value='チェックすると保存します。外すと未完了に戻せます。')
        ttk.Label(self.window,textvariable=self.notice,wraplength=590).pack(anchor='w',padx=20,pady=8)
        actions=ttk.Frame(self.window); actions.pack(fill='x',padx=20,pady=16)
        self.reload=ttk.Button(actions,text='読み直す',command=self.load); self.reload.pack(side='left')
        self.exit_button=ttk.Button(actions,text='閉じる',command=self.close); self.exit_button.pack(side='right')
        self.load(); self.state()
    def state(self):
        if not self.window.winfo_exists():
            return
        active=not self.app.busy and not self.app.closing
        for control in [self.reload,self.exit_button]+self.checks:
            control.configure(state='normal' if active else 'disabled')
    def run(self,operation,label):
        if self.app.busy or self.app.closing:
            return
        def work():
            try:
                result=(None,operation())
            except (OSError,ValueError) as exc:
                result=(str(exc),None)
            except Exception:
                result=('処理を完了できませんでした。記録を確認してください。',None)
            return complete,result
        def complete(result):
            if not self.window.winfo_exists():
                return
            error,snapshot=result
            if error:
                if self.snapshot:
                    for variable,flag in zip(self.variables,self.snapshot['done']):
                        variable.set(flag)
                self.notice.set('保存・読込に失敗しました：'+error)
            else:
                self.render(snapshot)
                self.notice.set('保存済みです。' if label=='完了状態を保存しています…' else 'チェックすると保存します。外すと未完了に戻せます。')
            self.state()
        if self.app.submit('plan_result',work,label):
            self.notice.set(label); self.state()
    def load(self):
        self.run(self.app.service.today_plan,'計画を読み込んでいます…')
    def render(self,snapshot):
        self.snapshot=snapshot
        for widget in self.body.winfo_children():
            widget.destroy()
        self.checks=[]; self.variables=[]
        if not snapshot:
            self.heading.set('今日の計画はまだありません。')
            ttk.Label(self.body,text='この画面を閉じ、左の「計画を作る」から作成してください。',wraplength=540).pack(anchor='w')
            self.summary.set(''); return
        plan=snapshot['plan']
        goal=plan['goal'] if len(plan['goal'])<=120 else plan['goal'][:120]+'…'
        self.heading.set(f"{plan['date']}（日本時間）\n{goal}")
        for i,(task,done) in enumerate(zip(plan['tasks'],snapshot['done'])):
            variable=tk.BooleanVar(value=done); self.variables.append(variable)
            row=ttk.Frame(self.body); row.pack(fill='x',pady=9)
            check=ttk.Checkbutton(row,variable=variable,command=lambda index=i:self.toggle(index))
            check.pack(side='left',anchor='n'); self.checks.append(check)
            ttk.Label(row,text=f"{i+1}. {task['title']}（{task['minutes']}分）",wraplength=490).pack(side='left',anchor='w')
        done=sum(snapshot['done']); total=len(plan['tasks'])
        self.summary.set(f'完了 {done} / {total}'+('  — 今日の計画はすべて完了です。' if done==total else ''))
    def toggle(self,index):
        if self.app.busy or not self.snapshot:
            return
        identifier=self.snapshot['id']; done=self.variables[index].get()
        self.run(lambda:self.app.service.set_completion(identifier,index,done),'完了状態を保存しています…')
    def close(self):
        if self.app.busy:
            self.notice.set('保存・読込が終わるまでお待ちください。'); return
        self.window.destroy()
