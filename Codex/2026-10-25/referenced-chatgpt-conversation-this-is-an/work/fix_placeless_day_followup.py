from pathlib import Path
p=Path('outputs/tomeris_context_boundaries.py');s=p.read_text(encoding='utf-8').replace("        weather=weather_request(text)","        day_only=re.fullmatch(r'(今日|明日|明後日)(?:は|の天気は|の天気)?[？?。！!]*',text.strip())\n        if day_only and self.pending_weather and not getattr(self,'last_weather_place',None):\n            self.pending_weather=day_only[1]\n            return text,self.track(text,day_only[1]+'の天気を調べる市区町村を入力してください。以前の地域を現在地として推測しません。')\n        weather=weather_request(text)")
p.write_text(s,encoding='utf-8')
