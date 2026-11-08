from pathlib import Path
p=Path('outputs');s=(p/'tomeris_desktop_v048.py').read_text(encoding='utf-8').replace('v0.48','v0.49').replace('from tomeris_collection_settings import','from tomeris_research_boundaries import')
(p/'tomeris_desktop_v049.py').write_text(s,encoding='utf-8')
