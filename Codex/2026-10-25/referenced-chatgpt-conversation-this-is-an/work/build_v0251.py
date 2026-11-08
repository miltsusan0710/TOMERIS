from pathlib import Path
s=Path('outputs/tomeris_desktop_v025.py').read_text(encoding='utf-8-sig').replace('v0.25','v0.25.1').replace('from tomeris_weather_service import DesktopService as PlanService','from tomeris_site_search import DesktopService as PlanService')
Path('outputs/tomeris_desktop_v0251.py').write_text(s,encoding='utf-8')
