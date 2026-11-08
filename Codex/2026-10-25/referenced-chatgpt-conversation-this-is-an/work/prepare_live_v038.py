from pathlib import Path
s=Path('work/check_source_reuse_live.py').read_text(encoding='utf-8').replace('tomeris_desktop_v037','tomeris_desktop_v038').replace('source_learning_live_check.json','source_learning_live_check_v038.json')
Path('work/check_source_reuse_live_v038.py').write_text(s,encoding='utf-8')
