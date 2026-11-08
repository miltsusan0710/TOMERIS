from pathlib import Path
s=Path('outputs/tomeris_desktop_v0251.py').read_text(encoding='utf-8-sig').replace('v0.25.1','v0.26').replace('from tomeris_site_search import DesktopService as PlanService','from tomeris_evidence_report import DesktopService as PlanService')
s=s.replace('検索：Bing／天気：Open-Meteoへ地域・座標を送信。保存済みの記憶は送りません。','調査：Bing検索＋公開ページ本文／天気：Open-Meteo。保存済みの記憶は外部に送りません。')
Path('outputs/tomeris_desktop_v026.py').write_text(s,encoding='utf-8')
