from pathlib import Path
s=Path('outputs/tomeris_desktop_v041.py').read_text(encoding='utf-8').replace('v0.41','v0.42').replace('from tomeris_tomorrow_plans import','from tomeris_source_followup import')
Path('outputs/tomeris_desktop_v042.py').write_text(s,encoding='utf-8')
