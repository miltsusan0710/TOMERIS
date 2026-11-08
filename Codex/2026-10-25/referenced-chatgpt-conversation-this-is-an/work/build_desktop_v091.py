from pathlib import Path
root=Path('outputs')
source=(root/'tomeris_desktop.py').read_text(encoding='utf-8-sig')
backup=root/'tomeris_desktop_v09.py'
if not backup.exists():
    backup.write_text(source,encoding='utf-8')
source=backup.read_text(encoding='utf-8-sig')
source=source.replace('from tomeris_desktop_service import DesktopService','from tomeris_plans import DesktopService, validate, today')
source=source.replace('v0.9','v0.9.1')
source=source.replace("buttons=[('記憶を確認'","buttons=[('計画を作る','plan'),('今日の計画','today'),('記憶を確認'")
source=source.replace('pady=11','pady=7').replace('pady=(4,28)','pady=(4,16)').replace('pady=(20,4)','pady=(12,4)')
source=source.replace("    def view(self,kind):\n        self.submit", "    def view(self,kind):\n        if kind=='plan':\n            self.plan_dialog(); return\n        self.submit")
source=source.replace("        self.memory_check.configure(state='normal' if active else 'disabled')", "        self.memory_check.configure(state='normal' if active else 'disabled')\n        dialog=getattr(self,'plan_window',None)\n        if dialog is not None and dialog.winfo_exists():\n            for control in self.plan_controls:\n                control.configure(state='normal' if active else 'disabled')")
source=source.replace("                    elif kind=='error':", "                    elif kind=='plan_result':\n                        callback,result=value\n                        callback(result)\n                    elif kind=='error':")
source=source.replace("                        self.entry.focus_set()", "                        if not (getattr(self,'plan_window',None) and self.plan_window.winfo_exists()):\n                            self.entry.focus_set()")
method='''    def plan_dialog(self):
        if self.busy or self.closing:
            return
        dialog=tk.Toplevel(self.root)
        self.plan_window=dialog
        dialog.title('今日の計画を作る')
        dialog.geometry('640x530'); dialog.minsize(600,510)
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

'''
source=source.replace('    def worker(self,data_dir,demo):',method+'    def worker(self,data_dir,demo):')
(root/'tomeris_desktop_v091.py').write_text(source,encoding='utf-8')
(root/'tomeris_desktop.py').write_text('"""Stable desktop shortcut entry point."""\nfrom tomeris_desktop_v091 import main\n\nif __name__ == "__main__":\n    main()\n',encoding='utf-8')
