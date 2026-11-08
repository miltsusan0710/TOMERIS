from pathlib import Path
p=Path('outputs/test_desktop_earthquake_followup.py');s=p.read_text(encoding='utf-8-sig').replace('{59-i:02}Z','{59-i:02}+09:00');p.write_text(s,encoding='utf-8')
