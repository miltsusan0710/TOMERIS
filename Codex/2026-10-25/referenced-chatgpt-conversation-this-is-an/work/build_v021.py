from pathlib import Path
source=Path('outputs/tomeris_desktop_v020.py').read_text(encoding='utf-8-sig')
source=source.replace('v0.20','v0.21').replace('from tomeris_memory_edit_ui import MemoryPanel','from tomeris_memory_restore_ui import MemoryPanel')
Path('outputs/tomeris_desktop_v021.py').write_text(source,encoding='utf-8')
