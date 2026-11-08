from pathlib import Path
p=Path('outputs');s=(p/'tomeris_desktop_v046.py').read_text(encoding='utf-8').replace('v0.46','v0.47').replace('from tomeris_persona import','from tomeris_public_learning import')
s=s.replace("menu.add_cascade(label='資料学習',menu=learning_menu)","learning_menu.add_command(label='自動収集の状態',command=lambda:self.auto_source_action('自動資料収集の状態'))\n        learning_menu.add_command(label='自動収集を停止',command=lambda:self.auto_source_action('自動資料収集を停止'))\n        learning_menu.add_command(label='自動収集を再開',command=lambda:self.auto_source_action('自動資料収集を再開'))\n        menu.add_cascade(label='資料学習',menu=learning_menu)")
s=s.replace('    def open_sources(self):', '''    def auto_source_action(self,text):
        if self.busy or self.closing or self.service is None:return
        self.submit('reply',lambda:self.service.chat(text,'unused'),'自動収集の設定を確認しています…')
    def auto_source_tick(self):
        if self.closing:return
        if self.service is not None and not self.busy and not self.entry.get('1.0','end').strip() and self.service.auto_sources_due():
            def work():return completed,self.service.collect_public_topic()
            def completed(result):
                if result:self.status.set(result)
            self.submit('plan_result',work,'公開資料を1件確認しています…')
        self.root.after(30000,self.auto_source_tick)
    def open_sources(self):''')
s=s.replace('        self.control_state()\n    def auto_source_action', '        self.control_state()\n        self.root.after(30000,self.auto_source_tick)\n    def auto_source_action',1)
(p/'tomeris_desktop_v047.py').write_text(s,encoding='utf-8')
