from pathlib import Path
s=Path('outputs/tomeris_desktop_v024.py').read_text(encoding='utf-8-sig').replace('v0.24','v0.24.1')
s=s.replace('from tomeris_capabilities import DesktopService as PlanService','from tomeris_weather_service import DesktopService as PlanService')
s=s.replace('検索先：Bing。天気の地域確認は直前の質問＋地域名。保存済みの記憶は送りません。','検索：Bing／天気：Open-Meteoへ地域・座標を送信。保存済みの記憶は送りません。')
s=s.replace('検索時は質問をBingへ送ります。天気の地域確認では直前の質問と地域名を組み合わせます。保存済みの記憶は送りません。','検索はBing、天気はOpen-Meteoを利用します。天気サービスへは入力した地域名と、その代表地点の座標を送ります。保存済みの記憶は送りません。')
Path('outputs/tomeris_desktop_v0241.py').write_text(s,encoding='utf-8')
