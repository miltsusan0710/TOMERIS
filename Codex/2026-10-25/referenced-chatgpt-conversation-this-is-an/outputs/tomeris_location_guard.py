"""Never infer a current location from chat history or model output."""
import re
from tomeris_auto_research_v029 import DesktopService as ResearchService


def asks_current_location(text):
    compact=re.sub(r'[\s。！？!?、,]','',text)
    return bool(re.search(r'現在地|今いる(?:場所|ところ)|今いる所|今の場所|ここ(?:の|で)(?:今日|明日)?(?:の)?天気',compact)) or bool(re.fullmatch(r'(?:ここ|今どこ|ここはどこ|私の場所)(?:で|は|です|でお願い|でお願いします|を教えて)?',compact))

class DesktopService(ResearchService):
    def location_reply(self,text):
        if not asks_current_location(text):return None
        weather=bool(self.pending_weather or re.search(r'天気|天候|予報',text))
        if weather:
            day='明後日' if '明後日' in text else ('明日' if '明日' in text else ('今日' if '今日' in text else self.pending_weather or '今日'))
            self.pending_weather=day
            return self.track(text,'現在地は取得していません。過去の会話や記憶から場所を推測することもできません。\n'+day+'の天気を調べる市区町村を入力してください。例：「平塚市」。日付の条件は保持しています。')
        return self.track(text,'現在地は取得していないため、どこにいるかは分かりません。現在のトメリスには位置情報を取得する機能はありません。天気を調べる場合は市区町村を入力してください。')
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        answer=self.location_reply(question)
        if answer is not None:return answer
        if self.pending_weather and re.fullmatch(r'(今日|明日|明後日)(?:は|の天気は|の天気)?[？?。！!]*',question.strip()):
            from tomeris_weather_service import DesktopService as WeatherService
            return WeatherService.web_chat(self,question,model,use_memory,automatic,progress)
        return super().web_chat(question,model,use_memory,automatic,progress)
    def chat(self,text,model,use_memory=False):
        answer=self.location_reply(text)
        if answer is not None:return answer
        return super().chat(text,model,use_memory)
    def report(self,question,progress=None,model=None):
        answer=self.location_reply(question)
        if answer is not None:return answer
        return super().report(question,progress,model)
