from pathlib import Path
p=Path('outputs/tomeris_weather_service.py');s=p.read_text(encoding='utf-8-sig')
backup=Path('outputs/tomeris_weather_service_before_v0311.py')
if not backup.exists():backup.write_text(s,encoding='utf-8')
s=s.replace("    if location_missing(compact): return ('','明日' if '明日' in compact else '今日')", "    if location_missing(compact): return ('','明日' if '明日' in compact else '今日')\n    prefix=re.match(r'^(今日|明日)(?:の)?\\s*(.+)$',compact)\n    leading_day=prefix[1] if prefix else None\n    if prefix:compact=prefix[2]")
s=s.replace("if place: return (place,match[2] or '今日')", "if place: return (place,leading_day or match[2] or '今日')")
p.write_text(s,encoding='utf-8')
s=Path('outputs/tomeris_desktop_v031.py').read_text(encoding='utf-8').replace('v0.31','v0.31.1')
Path('outputs/tomeris_desktop_v0311.py').write_text(s,encoding='utf-8')
