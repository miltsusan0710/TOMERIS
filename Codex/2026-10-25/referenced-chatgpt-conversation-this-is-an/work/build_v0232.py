from pathlib import Path
p=Path('outputs/tomeris_desktop_v0231.py')
s=p.read_text(encoding='utf-8-sig').replace('v0.23.1','v0.23.2').replace('from tomeris_web_search import DesktopService as PlanService','from tomeris_weather_followup import DesktopService as PlanService')
s=s.replace('検索時は今回の質問をBingへ送ります。記憶や過去の会話は送りません。','検索時は質問をBingへ送ります。天気の地域確認では直前の質問と地域名を組み合わせます。保存済みの記憶は送りません。')
s=s.replace('検索時は今回の質問をBingへ送ります。記憶・過去会話は送りません。','検索先：Bing。天気の地域確認は直前の質問＋地域名。保存済みの記憶は送りません。')
Path('outputs/tomeris_desktop_v0232.py').write_text(s,encoding='utf-8')
