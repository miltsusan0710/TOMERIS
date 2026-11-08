from pathlib import Path
s=Path('outputs/tomeris_desktop_v039.py').read_text(encoding='utf-8').replace('v0.39','v0.40').replace('from tomeris_schedule_grounding import','from tomeris_dated_schedule import')
Path('outputs/tomeris_desktop_v040.py').write_text(s,encoding='utf-8')
