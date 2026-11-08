from pathlib import Path
s=Path('outputs/tomeris_desktop_v0241.py').read_text(encoding='utf-8-sig').replace('v0.24.1','v0.25')
s=s.replace('import argparse','import argparse\nfrom tomeris_orb import Orb',1)
s=s.replace("self.root.geometry('1080x760')","self.root.geometry('1120x850')").replace("self.root.minsize(860,600)","self.root.minsize(880,760)")
start=s.index('    def make_ui(self):');end=s.index('    def open_source(self,url):')
s=s[:start]+Path('work/bright_ui_method.txt').read_text(encoding='utf-8-sig')+'\n'+s[end:]
s=s.replace("self.transcript.insert('end',text+'\\n\\n','body')","self.transcript.insert('end',text+'\\n\\n','body_you' if title=='あなた' else ('body_notice' if title=='お知らせ' else 'body_assistant'))")
Path('outputs/tomeris_desktop_v025.py').write_text(s,encoding='utf-8')
