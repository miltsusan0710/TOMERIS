from pathlib import Path
s=Path('outputs/tomeris_desktop_v030.py').read_text(encoding='utf-8').replace('from tomeris_auto_research_v029 import','from tomeris_location_guard import').replace('v0.30','v0.30.1')
Path('outputs/tomeris_desktop_v0301.py').write_text(s,encoding='utf-8')
