from pathlib import Path
p=Path('outputs');s=(p/'tomeris_desktop_v044.py').read_text(encoding='utf-8').replace('v0.44','v0.45').replace('from tomeris_research_retry import','from tomeris_persona import')
(p/'tomeris_desktop_v045.py').write_text(s,encoding='utf-8')
