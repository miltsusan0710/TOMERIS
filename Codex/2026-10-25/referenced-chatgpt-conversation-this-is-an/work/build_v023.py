from pathlib import Path
s=Path('outputs/tomeris_desktop_v022.py').read_text(encoding='utf-8-sig').replace('v0.22','v0.23')
s=s.replace('from tomeris_memory_edit import DesktopService as PlanService','from tomeris_web_search import DesktopService as PlanService')
s=s.replace("values=['会話','2モデル比較']","values=['会話','会話＋自動検索','ネット検索','2モデル比較']")
s=s.replace("        else:\n            func=lambda:self.service.chat(question,model,use_memory)","        elif self.mode.get() in ('会話＋自動検索','ネット検索'):\n            automatic=self.mode.get()=='会話＋自動検索'\n            func=lambda:self.service.web_chat(question,model,use_memory,automatic,lambda s:self.events.put(('progress',s)))\n            label='検索の必要性を確認しています…'\n        else:\n            func=lambda:self.service.chat(question,model,use_memory)")
s=s.replace("        self.memory_check.configure(state='normal' if active else 'disabled')","        self.memory_check.configure(state='normal' if active and self.mode.get()!='ネット検索' else 'disabled')\n        if self.mode.get() in ('会話＋自動検索','ネット検索') and not self.busy:\n            self.status.set('検索時は今回の質問をBingへ送ります。記憶・過去会話は送りません。')")
Path('outputs/tomeris_desktop_v023.py').write_text(s,encoding='utf-8')
