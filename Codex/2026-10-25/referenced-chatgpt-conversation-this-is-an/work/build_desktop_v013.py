from pathlib import Path
root=Path('outputs')
s=(root/'tomeris_plan_history_ui.py').read_text(encoding='utf-8-sig')
s=s.replace("        self.exit_button=ttk.Button(self.window,text='閉じる',command=self.close); self.exit_button.pack(anchor='e',padx=20,pady=(0,16))", "        footer=ttk.Frame(self.window); footer.pack(fill='x',padx=20,pady=(0,16))\n        self.carry_button=ttk.Button(footer,text='残った行動を今日の下書きに',command=self.carry)\n        self.carry_button.pack(side='left')\n        self.exit_button=ttk.Button(footer,text='閉じる',command=self.close); self.exit_button.pack(side='right')")
s=s.replace('[self.reload,self.exit_button,self.list]', '[self.reload,self.exit_button,self.list,self.carry_button]')
s=s.replace("            self.text(describe(self.visible[selected[0]]))", "            self.text(describe(self.visible[selected[0]]).replace('この画面は閲覧専用です。チェックの変更は「今日の計画」で行ってください。','元の計画は変更しません。下書きを作った後、確認して保存できます。'))")
method='''    def carry(self):
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
'''
s=s.replace('    def close(self):',method+'    def close(self):')
(root/'tomeris_plan_history_ui_v013.py').write_text(s,encoding='utf-8')
s=(root/'tomeris_desktop_v012.py').read_text(encoding='utf-8-sig').replace('v0.12','v0.13')
s=s.replace('from tomeris_plan_history import DesktopService as PlanService','from tomeris_plan_carry import DesktopService as PlanService')
s=s.replace('from tomeris_plan_history_ui import PlanHistoryPanel','from tomeris_plan_history_ui_v013 import PlanHistoryPanel')
s=s.replace('    def plan_dialog(self):','    def plan_dialog(self,initial=None):')
s=s.replace("dialog.geometry('640x530'); dialog.minsize(600,510)","dialog.geometry('680x620'); dialog.minsize(620,600)")
s=s.replace("        def inputs():", "        if initial is not None:\n            dialog.title('今日の計画・引き継ぎ下書き（未保存）')\n            goal.insert('1.0',initial['goal'])\n            budget.set(str(initial['budget']))\n            for i,task in enumerate(initial['tasks']):\n                rows[i][0].set(task['title']); rows[i][1].set(str(task['minutes']))\n            notice.set(initial['notice'])\n        def inputs():")
(root/'tomeris_desktop_v013.py').write_text(s,encoding='utf-8')
