"""Explicit task selection and confirmation before carrying plans to tomorrow."""
import tkinter as tk
from tkinter import ttk,messagebox
from tomeris_plan_history_ui_v015 import PlanHistoryPanel as BasePanel

class PlanHistoryPanel(BasePanel):
    def __init__(self,app):
        super().__init__(app)
        self.tomorrow_button=ttk.Button(self.window,text='残った行動を明日の下書きに',command=self.tomorrow)
        self.tomorrow_button.grid(row=6,column=0,sticky='w',padx=20,pady=(0,12));self.state()
    def state(self):
        super().state()
        if hasattr(self,'tomorrow_button') and self.window.winfo_exists():
            self.tomorrow_button.configure(state='disabled' if self.app.busy or self.app.closing else 'normal')
    def tomorrow(self):
        if self.app.busy or self.app.closing:return
        selected=self.list.curselection()
        if not selected:self.message.set('引き継ぎ元の計画を選んでください。');return
        identifier=self.visible[selected[0]]['id']
        def work():
            try:result=(None,self.app.service.tomorrow_draft(identifier))
            except (ValueError,OSError) as exc:result=(str(exc),None)
            return ready,result
        def ready(result):
            error,draft=result
            if error:self.message.set(error);return
            self.review(draft)
        self.app.submit('plan_result',work,'明日の下書きを準備しています…')
    def review(self,draft):
        window=tk.Toplevel(self.window);window.title('明日への引き継ぎを確認');window.geometry('640x420');window.transient(self.window);window.grab_set()
        ttk.Label(window,text='保存先：'+draft['date'],font=('Yu Gothic UI',14,'bold')).pack(anchor='w',padx=20,pady=12)
        notice='完了チェック済みの行動は除外しています。' if draft['recorded'] else '完了チェックの記録がありません。実際に残っている行動だけ選んでください。'
        if draft['existing']:notice+='\n対象日には計画があります。保存すると新しい改訂になり、以前の計画も履歴に残ります。'
        ttk.Label(window,text=notice,wraplength=580).pack(anchor='w',padx=20,pady=6)
        choices=[]
        for task in draft['tasks']:
            v=tk.BooleanVar(value=True);choices.append(v)
            tk.Checkbutton(window,text=f"{task['title']}（{task['minutes']}分）",variable=v,wraplength=560).pack(anchor='w',padx=20,pady=7)
        status=tk.StringVar();ttk.Label(window,textvariable=status,wraplength=580).pack(anchor='w',padx=20,pady=8)
        bar=ttk.Frame(window);bar.pack(side='bottom',fill='x',padx=20,pady=15)
        def close():
            if not self.app.busy:window.destroy();self.window.grab_set()
        window.protocol('WM_DELETE_WINDOW',close)
        def save():
            if self.app.busy:return
            indices=[i for i,v in enumerate(choices) if v.get()]
            if not indices:status.set('行動を1つ以上選んでください。');return
            if not messagebox.askyesno('保存の確認',draft['date']+'の計画として選択した行動を保存しますか？',parent=window):return
            def work():
                try:result=(None,self.app.service.save_tomorrow_draft(draft['token'],indices))
                except (ValueError,OSError) as exc:result=(str(exc),None)
                return saved,result
            def saved(result):
                error,message=result
                if error:status.set(error);button.configure(state='normal');return
                window.destroy();self.window.grab_set();self.message.set(message);self.load()
            button.configure(state='disabled');self.app.submit('plan_result',work,'明日の計画を保存しています…')
        button=ttk.Button(bar,text='選んだ行動を保存',command=save);button.pack(side='left')
        ttk.Button(bar,text='キャンセル',command=close).pack(side='right')

