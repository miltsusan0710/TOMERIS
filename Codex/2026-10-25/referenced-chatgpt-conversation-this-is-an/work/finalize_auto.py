from pathlib import Path
p=Path('outputs/tomeris_auto_research.py');s=p.read_text(encoding='utf-8-sig').replace('browser_search_url\n','browser_search_url, wikipedia_search\n').replace("'wikipedia英語':'Wikipedia（日英）','英語版wikipedia':'Wikipedia（日英）'", "'wikipedia英語':'Wikipedia（英語）','英語版wikipedia':'Wikipedia（英語）'")
s=s.replace("        if self.mode!='自動':return super().candidates(text)","        if self.mode=='Wikipedia（英語）':\n            try:return wikipedia_search(text,'en'),['指定方法：Wikipedia英語']\n            except MethodError as exc:return [],['Wikipedia英語：'+str(exc)]\n        if self.mode!='自動':return super().candidates(text)")
p.write_text(s,encoding='utf-8')
s=Path('work/check_methods_ui.py').read_text(encoding='utf-8-sig').replace('v027','v028')
Path('work/check_auto_methods_ui.py').write_text(s,encoding='utf-8')
