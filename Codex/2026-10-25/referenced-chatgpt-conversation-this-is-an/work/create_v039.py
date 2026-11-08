from pathlib import Path
p=Path('outputs/tomeris_desktop_v038.py')
s=p.read_text(encoding='utf-8').replace('v0.38','v0.39').replace('from tomeris_prose_evidence import','from tomeris_schedule_grounding import')
Path('outputs/tomeris_desktop_v039.py').write_text(s,encoding='utf-8')
