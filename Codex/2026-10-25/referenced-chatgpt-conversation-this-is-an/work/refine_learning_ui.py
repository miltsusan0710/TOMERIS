from pathlib import Path
p=Path('outputs/tomeris_research_learning.py');s=p.read_text(encoding='utf-8')
s='import re\nfrom tomeris_search_methods import brave_search\nfrom tomeris_web_search import search_web,SearchError\nfrom tomeris_search_methods import MethodError\n'+s
s=s.replace("        rows,notes=super().candidates(text)","        fresh=bool(re.search(r'今の|今起き|現在|最新|速報|直近|さっき|今日|ニュース|運行|遅延',self.question_context or text))\n        if self.mode=='自動' and fresh:\n            name='Brave API' if self.brave_key else 'Bing RSS（試験）'\n            try:rows=brave_search(text,self.brave_key) if self.brave_key else search_web(text)\n            except (MethodError,SearchError) as exc:return [],['最新情報の検索：'+name+'／'+str(exc),'百科事典や保存資料への代替はしていません。']\n            return rows,['最新情報の検索：'+name,'記事の更新日だけで出来事の発生日時を確認したとは扱いません。']\n        rows,notes=super().candidates(text)")
p.write_text(s,encoding='utf-8')
p=Path('outputs/tomeris_desktop_v033.py');s=p.read_text(encoding='utf-8')
s=s.replace("        menu.add_cascade(label='表示',menu=view_menu)","        menu.add_cascade(label='表示',menu=view_menu)\n        learning_menu=tk.Menu(menu,tearoff=False)\n        for label,command in [('学習した資料を見る','学習した資料を見せて'),('資料学習を停止','ネット学習を停止'),('資料学習を再開','ネット学習を再開'),('保存した資料を消去','学習した資料を消去')]:\n            learning_menu.add_command(label=label,command=lambda q=command:self.learning_action(q))\n        menu.add_cascade(label='資料学習',menu=learning_menu)")
s=s.replace('    def update_chat_layout(self):',"    def learning_action(self,question):\n        if self.busy or self.closing or self.service is None:return\n        self.submit('reply',lambda:self.service.special(question),'資料学習の状態を確認しています…')\n    def update_chat_layout(self):")
p.write_text(s,encoding='utf-8')
