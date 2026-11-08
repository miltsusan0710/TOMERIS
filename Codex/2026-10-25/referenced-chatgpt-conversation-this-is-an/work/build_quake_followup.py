from pathlib import Path
s=Path('outputs/tomeris_desktop_v035.py').read_text(encoding='utf-8').replace('v0.35','v0.36').replace('from tomeris_source_management import','from tomeris_earthquake_followup import')
Path('outputs/tomeris_desktop_v036.py').write_text(s,encoding='utf-8')
