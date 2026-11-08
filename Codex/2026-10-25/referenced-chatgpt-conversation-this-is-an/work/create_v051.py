from pathlib import Path
p=Path('outputs');s=(p/'tomeris_desktop_v050.py').read_text(encoding='utf-8').replace('v0.50','v0.51').replace('from tomeris_editable_collection import','from tomeris_parallel_collection import').replace('公開資料を1件確認しています…','公開資料を最大2テーマ確認しています…')
(p/'tomeris_desktop_v051.py').write_text(s,encoding='utf-8')
