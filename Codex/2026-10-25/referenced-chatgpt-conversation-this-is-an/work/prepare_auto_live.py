from pathlib import Path
s=Path('work/check_multisearch_live.py').read_text(encoding='utf-8-sig').replace('tomeris_multisearch_service','tomeris_auto_research_v0281').replace('multisearch_live_report.txt','auto_research_v0281_live_report.txt')
Path('work/check_auto_fixes_live.py').write_text(s,encoding='utf-8')
