"""Weather routing stays active across a failed lookup and successive region replies."""
import re
from tomeris_capabilities import DesktopService as CapabilitiesService
from tomeris_weather_followup import region_reply
from tomeris_web_search import location_missing
from tomeris_weather_data import fetch_weather,WeatherError


def weather_request(text):
    compact=text.strip().rstrip('？?。!！')
    if location_missing(compact): return ('','明日' if '明日' in compact else '今日')
    match=re.fullmatch(r'(.+?)(?:の)?(今日|明日)?(?:の)?(?:天気予報|天気|天候)(?:は|を)?(?:教えて|調べて|検索して|教えてください)?',compact)
    if match:
        place=region_reply(match[1].rstrip('の'))
        if place: return (place,match[2] or '今日')
    return None

class DesktopService(CapabilitiesService):
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        request=weather_request(question)
        region=region_reply(question) if self.pending_weather else None
        if request is not None or region:
            place,day=request if request is not None else (region,self.pending_weather)
            self.pending_weather=day
            if not place:
                return self.track(question,'どの市区町村の天気を調べますか？「平塚市」「東京都荒川区」のように地域名で答えてください。天気サービスへ地域名と、その代表地点の座標だけを送ります。')
            if progress: progress(f'{place}の{day}の予報をOpen-Meteoから取得しています…')
            if self.demo: return self.track(question,f'画面確認用：{place}の{day}の予報。実際の天気は取得していません。')
            try: answer=fetch_weather(place,day)
            except WeatherError as exc:
                return self.track(question,f'{place}の{day}の予報を取得できませんでした。\n{exc}\n天気の話題を保持しています。「荒川区」など別の地域名だけでも再試行できます。')
            return self.save_answer(question,answer)
        self.pending_weather=None
        return super().web_chat(question,model,use_memory,automatic,progress)
