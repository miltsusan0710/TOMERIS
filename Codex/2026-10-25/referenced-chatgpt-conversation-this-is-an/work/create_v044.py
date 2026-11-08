from pathlib import Path
p=Path('outputs');s=(p/'tomeris_desktop_v043.py').read_text(encoding='utf-8').replace('v0.43','v0.44').replace('from tomeris_research_history_service import','from tomeris_research_retry import')
(p/'tomeris_desktop_v044.py').write_text(s,encoding='utf-8')
