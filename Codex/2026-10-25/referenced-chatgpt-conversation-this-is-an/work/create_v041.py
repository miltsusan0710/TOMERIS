from pathlib import Path
s=Path('outputs/tomeris_desktop_v040.py').read_text(encoding='utf-8').replace('v0.40','v0.41').replace('from tomeris_dated_schedule import','from tomeris_tomorrow_plans import').replace('from tomeris_plan_history_ui_v015 import','from tomeris_tomorrow_ui import')
Path('outputs/tomeris_desktop_v041.py').write_text(s,encoding='utf-8')
