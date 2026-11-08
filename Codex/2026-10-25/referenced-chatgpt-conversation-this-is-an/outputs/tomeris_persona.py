"""Restrained local-chat character; deterministic reports are never rewritten."""
import re
from tomeris_research_retry import DesktopService as BaseService
BASE='\nあなたはトメリス。落ち着きと機転のある専属AIアシスタントとして、自然な敬語で端的に話す。相手の意図をくみ、必要なら次の一歩を提案する。芝居がかった呼称・過剰な称賛・定型の決めぜりふは使わない。実在の感情・意識や未実行の操作を主張せず、不明な事実や予定を作らない。'
SERIOUS=re.compile(r'地震|災害|津波|警報|けが|怪我|痛|病|薬|死|つら|辛|苦し|不安|悩|失敗|困|事故|緊急|お金|借金|契約|法律|出典|調査|予定|計算|正確|真面目|まじめ|冗談抜き|ジョークなし')
CASUAL=re.compile(r'雑談|ひま|暇|退屈|面白|楽しい|ひと息|一息|休憩|ジョーク|冗談')
class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.persona_chat_count=0;self.last_humor_opportunity=-10
    def conversation_persona(self,text):
        self.persona_chat_count+=1
        allow=bool(CASUAL.search(text)) and not SERIOUS.search(text) and self.persona_chat_count-self.last_humor_opportunity>=5
        if allow:
            self.last_humor_opportunity=self.persona_chat_count
            return BASE+'今の軽い会話では、自然に合う場合だけ短い機知を一言添えてよい。無理に笑わせず、皮肉で相手を下げない。ジョークを入れなくてもよい。'
        return BASE+'今回はジョークや皮肉を加えず、要点に自然に答える。'
