from pathlib import Path
p=Path('outputs/tomeris_desktop_v016.py')
s=p.read_text(encoding='utf-8-sig').replace('from datetime import datetime','from datetime import datetime, timezone, timedelta')
s=s.replace("datetime.now().strftime('%Y%m%d_%H%M%S')", "datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d_%H%M%S')")
s=s.replace("defaultextension='.zip',initialfile=", "confirmoverwrite=False,defaultextension='.zip',initialfile=")
p.write_text(s,encoding='utf-8')
