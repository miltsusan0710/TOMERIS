from pathlib import Path
p=Path('outputs')
s=(p/'tomeris_backup_v048.py').read_text(encoding='utf-8').replace("'auto_collection.json')","'auto_collection.json','auto_topics.json')").replace('MAX_FILE_BYTES=','from tomeris_topic_settings import validate_topics\nMAX_FILE_BYTES=',1)
s=s.replace("name=='auto_collection.json' else MAX_FILE_BYTES","name in ('auto_collection.json','auto_topics.json') else MAX_FILE_BYTES")
s=s.replace("if name=='auto_collection.json':validate_settings(data)","if name=='auto_collection.json':validate_settings(data)\n            if name=='auto_topics.json':validate_topics(data)").replace("'app_version':'0.48'","'app_version':'0.50'")
(p/'tomeris_backup_v050.py').write_text(s,encoding='utf-8')
s=(p/'tomeris_restore_v048.py').read_text(encoding='utf-8').replace('tomeris_backup_v048','tomeris_backup_v050').replace('MAX_ARCHIVE_BYTES=','from tomeris_topic_settings import validate_topics\nMAX_ARCHIVE_BYTES=',1)
s=s.replace("entry.filename=='auto_collection.json'","entry.filename in ('auto_collection.json','auto_topics.json')").replace("name=='auto_collection.json' else MAX_FILE_BYTES","name in ('auto_collection.json','auto_topics.json') else MAX_FILE_BYTES")
s=s.replace("elif name=='daily_plans.json':","elif name=='auto_topics.json':\n                    validate_topics(document)\n                    counts['auto_topics']=len(document['topics'])\n                elif name=='daily_plans.json':")
(p/'tomeris_restore_v050.py').write_text(s,encoding='utf-8')
s=(p/'tomeris_desktop_v049.py').read_text(encoding='utf-8').replace('v0.49','v0.50').replace('from tomeris_research_boundaries import','from tomeris_editable_collection import').replace('from tomeris_backup_v048 import','from tomeris_backup_v050 import').replace('from tomeris_restore_v048 import','from tomeris_restore_v050 import')
s=s.replace('from tomeris_sources_ui import SourcesPanel','from tomeris_sources_ui import SourcesPanel\nfrom tomeris_collection_ui import CollectionPanel')
s=s.replace("menu.add_cascade(label='資料学習',menu=learning_menu)","learning_menu.add_command(label='自動収集のテーマ・結果',command=self.open_collection)\n        menu.add_cascade(label='資料学習',menu=learning_menu)")
s=s.replace('    def control_state(self):','''    def open_collection(self):
        if self.busy or self.closing:return
        panel=getattr(self,'collection_panel',None)
        if panel and panel.window.winfo_exists():panel.window.lift();return
        self.collection_panel=CollectionPanel(self)
    def control_state(self):
        panel=getattr(self,'collection_panel',None)
        if panel:panel.state()''',1)
(p/'tomeris_desktop_v050.py').write_text(s,encoding='utf-8')
