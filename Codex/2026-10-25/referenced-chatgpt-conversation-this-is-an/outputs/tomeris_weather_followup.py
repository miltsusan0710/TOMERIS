"""Carry only an explicitly requested weather region clarification between turns."""
import re
from tomeris_web_search import DesktopService as SearchService, location_missing


def region_reply(text):
    text=text.strip().rstrip('。.!！?？')
    text=re.sub(r'(です|でお願いします|をお願いします|お願いします)$','',text).strip()
    if len(text)>40 or not text: return None
    if re.fullmatch(r'[一-龥々ぁ-んァ-ヶー]+(?:都|道|府|県|市|区|町|村)',text): return text
    if text in ('東京','大阪','京都','横浜','名古屋','札幌','仙台','福岡','神戸'): return text
    return None

class DesktopService(SearchService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.pending_weather=None
    def chat(self,*args,**kwargs):
        self.pending_weather=None
        return super().chat(*args,**kwargs)
    def compare(self,*args,**kwargs):
        self.pending_weather=None
        return super().compare(*args,**kwargs)
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        question=question.strip()
        previous=self.pending_weather
        self.pending_weather=None
        if location_missing(question):
            self.pending_weather='明日の天気' if '明日' in question else ('今日の天気' if any(t in question for t in ('今日','今','現在')) else '天気')
            return 'どの市区町村の天気を調べますか？「荒川区」のように地域名だけで答えられます。次に送った地域名と、この天気の質問を組み合わせて検索します。'
        region=region_reply(question) if previous else None
        if region:
            query=f'{region}の{previous}'
            if progress: progress('天気の地域として受け取りました：'+query)
            answer=super().web_chat(query,model,False,False,progress)
            return f'検索する内容：{query}\n\n'+answer
        return super().web_chat(question,model,use_memory,automatic,progress)

