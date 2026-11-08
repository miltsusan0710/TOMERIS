from pathlib import Path
s=Path('work/check_location_guard_ui.py').read_text(encoding='utf-8-sig').replace('tomeris_desktop_v0301','tomeris_desktop_v031');Path('work/check_v031_weather.py').write_text(s,encoding='utf-8')
s=Path('work/check_hud_chat_ui.py').read_text(encoding='utf-8-sig').replace('tomeris_desktop_v030','tomeris_desktop_v031');Path('work/check_v031_chat.py').write_text(s,encoding='utf-8')
