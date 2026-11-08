"""Reset only obsolete tool context at explicit topic boundaries."""
import re
from tomeris_earthquake_followup import DesktopService as BaseService,recent_earthquake
from tomeris_auto_research_v029 import instruction,more_information
from tomeris_weather_service import weather_request
from tomeris_calculator import expression_from,CalculationError

MANAGEMENT=('学習した資料を見せて','学習状況を教えて','ネット学習を停止','ネット学習を再開','学習した資料を消去','会話の好みを教えて','覚えた会話の好みを教えて','会話の好みをリセット','会話の好みを標準に戻して')
def preference_request(text):return bool(re.fullmatch(r'(?:今後は|これからは|いつも)?(?:回答|返答|説明)(?:は|を)(?:短く|簡潔に|詳しく)(?:して|してください|お願い|お願いします)[。！!]*',text.strip()))

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self._context_depth=0
    def clear_tool_context(self):
        self.pending_method=None;self.pending_subject=False;self.pending_weather=None;self.last_weather_place=None
        self.last_research_request=None;self.followup_seen_urls=set();self.earthquake_record=None
    def prepare_context(self,text):
        compact=text.strip().rstrip('？?。！!')
        if compact in ('キャンセル','やめる','中止'):
            self.clear_tool_context()
            return text,self.track(text,'確認待ちと調査の引き継ぎを取り消しました。新しい質問を入力してください。')
        changed=re.match(r'^(?:話題を変えて|別の話題にして|別の話題)[、,:：\s]*(.*)$',text.strip())
        if changed:
            self.clear_tool_context();self.session_turns=[]
            text=changed[1].strip()
            if not text:return text,self.track('話題を変えて','新しい話題に切り替えました。質問や相談を入力してください。')
        selected,topic=instruction(text)
        if selected and more_information(topic) and self.last_research_request:
            self.pending_method=None;self.pending_subject=False;self.pending_weather=None;self.last_weather_place=None;self.earthquake_record=None
            return text,None
        if selected:
            # A new named provider must not inherit an unrelated weather or earthquake.
            self.clear_tool_context()
            return text,None
        if compact in MANAGEMENT or preference_request(text):
            self.clear_tool_context();return text,None
        try:is_math=expression_from(text) is not None
        except CalculationError:is_math=True
        if is_math:
            self.clear_tool_context();return text,self.arithmetic(text)
        if recent_earthquake(text):
            self.pending_method=None;self.pending_subject=False;self.pending_weather=None;self.last_weather_place=None;self.last_research_request=None
            return text,None
        day_only=re.fullmatch(r'(今日|明日|明後日)(?:は|の天気は|の天気)?[？?。！!]*',text.strip())
        if day_only and self.pending_weather and not getattr(self,'last_weather_place',None):
            self.pending_weather=day_only[1]
            return text,self.track(text,day_only[1]+'の天気を調べる市区町村を入力してください。以前の地域を現在地として推測しません。')
        weather=weather_request(text)
        if weather is not None:
            self.pending_method=None;self.pending_subject=False;self.last_research_request=None;self.earthquake_record=None
            # A new place-less question must not silently reuse an older place.
            if not weather[0]:self.last_weather_place=None
            return text,None
        if more_information(text) and self.earthquake_record is not None:return '地震の続報は？',None
        if more_information(text) and self.pending_weather:
            return text,self.track(text,'天気のどの情報を確認しますか？「明後日は？」や市区町村名で続けられます。現在表示できるのは天気・最高最低気温・降水確率です。')
        if compact in ('こんにちは','おはよう','こんばんは','ありがとう','おやすみ'):
            self.clear_tool_context()
        return text,None
    def context_call(self,text,call):
        if self._context_depth:return call(text)
        self._context_depth+=1
        try:
            query,answer=self.prepare_context(text)
            return answer if answer is not None else call(query)
        finally:self._context_depth-=1
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        return self.context_call(question,lambda q:super(DesktopService,self).web_chat(q,model,use_memory,automatic,progress))
    def chat(self,text,model,use_memory=False):
        return self.context_call(text,lambda q:super(DesktopService,self).chat(q,model,use_memory))
    def report(self,question,progress=None,model=None):
        return self.context_call(question,lambda q:super(DesktopService,self).report(q,progress,model))
    def special(self,text):
        if text.strip().rstrip('。！!') in MANAGEMENT:self.clear_tool_context()
        return super().special(text)
