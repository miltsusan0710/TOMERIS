from pathlib import Path
p=Path('outputs/tomeris_auto_research_v0281.py');s=p.read_text(encoding='utf-8').replace('from datetime import datetime\n','').replace('from tomeris_strict_evidence import terms\n','').replace('from urllib.parse import urlsplit\n','')
s=s.replace("    text=text.strip()\n", "    text=text.strip()\n    if re.match(r'^('+NAMES+r')で(?:できる|何ができる|使える)',text,re.I):return None,text\n    if re.search(r'('+NAMES+r')(?:と|・|、|及び)('+NAMES+r')(?:だけ)?で',text,re.I):return '要確認',text\n",1)
p.write_text(s,encoding='utf-8')
p=Path('outputs/test_desktop_research_followup.py');s=p.read_text(encoding='utf-8-sig');s=s.replace("                # The middle form isn't an understood prefix; use a directly conflicting form below.\n                if text=='GoogleとWikipediaで調べて':continue\n",'');p.write_text(s,encoding='utf-8')
s=Path('work/check_auto_methods_ui.py').read_text(encoding='utf-8').replace('v028','v0281');Path('work/check_auto_fixes_ui.py').write_text(s,encoding='utf-8')
