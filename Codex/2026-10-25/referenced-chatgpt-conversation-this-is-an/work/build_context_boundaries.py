from pathlib import Path
s=Path('outputs/tomeris_desktop_v036.py').read_text(encoding='utf-8').replace('v0.36','v0.37').replace('from tomeris_earthquake_followup import','from tomeris_context_boundaries import')
Path('outputs/tomeris_desktop_v037.py').write_text(s,encoding='utf-8')
