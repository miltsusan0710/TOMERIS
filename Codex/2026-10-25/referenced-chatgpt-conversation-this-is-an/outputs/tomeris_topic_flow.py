"""General, bounded follow-up routing; facts are retrieved, not inferred from answers."""
import re,time
from tomeris_school_context import DesktopService as BaseService,PRINCIPAL
from tomeris_school_location import subject as school_subject
from tomeris_auto_research_v029 import instruction
from tomeris_source_followup import SOURCE_REQUEST
from tomeris_capabilities import DesktopService as ConversationService

FOLLOW=re.compile(r'(?:それの|その|そこの)?(使い方|料金|価格|値段|所在地|創業者|開発者|社長|メリット|デメリット|特徴|注意点|歴史|発売日|設立日)(?:は|を教えて|を教えてください)?[？?。！!]*')
MORE=re.compile(r'(?:もっと|さらに)?(?:詳しく|ほかには|他には|他の情報は|続けて|続きを教えて)(?:教えて|調べて|ください)?[？?。！!]*')
WHEN=re.compile(r'(?:それは)?いつ(?:できた|作られた|設立された|発売された)(?:の|んですか)?[？?。！!]*')

def continuation(text):
    text=text.strip()
    match=FOLLOW.fullmatch(text)
    if match:return match[1]
    if MORE.fullmatch(text):return '詳しい情報'
    if WHEN.fullmatch(text):return '成立・設立・発売の時期'
    return None

def topic_choices(topic):
    # Only an explicit two-item Japanese conjunction; do not invent entities.
    match=re.fullmatch(r'([^と、\n]{1,60})と([^と、\n]{1,60}?)(?:の比較|の違い|を比較)?',topic)
    if not match:return []
    parts=[part.strip() for part in match.groups()]
    return parts if all(parts) and parts[0]!=parts[1] else []

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.flow_topic=None;self.flow_time=0;self.flow_resolving=False;self.flow_choice=None
    def clear_tool_context(self):
        self.flow_topic=None;self.flow_time=0;self.flow_choice=None
        return super().clear_tool_context()
    def ordinary_followup(self,text):
        selected,phrase=instruction(text)
        return (not selected and MORE.fullmatch(phrase.strip()) and not self.flow_topic
                and bool(self.session_turns) and not self.last_research_request
                and not self.pending_weather and not self.pending_method and self.earthquake_record is None)
    def chat(self,text,model,use_memory=False):
        if self.ordinary_followup(text):return ConversationService.chat(self,text,model,use_memory)
        return super().chat(text,model,use_memory)
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        if self.ordinary_followup(question):return ConversationService.chat(self,question,model,use_memory)
        return super().web_chat(question,model,use_memory,automatic,progress)
    def report(self,question,progress=None,model=None):
        result=super().report(question,progress,model)
        if not self.flow_resolving:
            _,topic=instruction(question)
            topic=re.sub(r'^(?:調査|検索)[:：]\s*','',topic.strip())
            topic=re.sub(r'(?:について)?(?:調べて|検索して|教えて)(?:ください)?[。！？!?]*$','',topic).strip()
            if topic and len(topic)<=180 and not continuation(topic) and not re.search(r'https?://',topic):
                self.flow_topic=topic;self.flow_time=time.monotonic()
        return result
    def school_location(self,text,model=None,progress=None):
        result=super().school_location(text,model,progress)
        name=school_subject(instruction(text)[1])
        if name:self.flow_topic=name;self.flow_time=time.monotonic()
        return result
    def prepare_context(self,text):
        if self.flow_resolving:return super().prepare_context(text)
        pending=self.flow_choice;self.flow_choice=None
        if pending and text.strip().rstrip('。！？!?') in pending['choices']:
            if time.monotonic()-pending['time']>600:
                self.clear_tool_context()
                return text,self.track(text,'対象の確認が時間切れです。対象名と知りたい内容をもう一度入力してください。')
            self.flow_topic=text.strip().rstrip('。！？!?');self.flow_time=time.monotonic()
            return self.prepare_context(pending['question'])
        selected,phrase=instruction(text);compact=phrase.strip().rstrip('。！？!?')
        aspect=continuation(phrase)
        if self.flow_topic and time.monotonic()-self.flow_time>600:
            # Older research layers also retain the previous request. Expire those
            # together so they cannot silently revive an expired subject.
            self.clear_tool_context()
            if aspect:
                return text,self.track(text,'前の調査から時間が空いたため、続けて調べる対象を確認させてください。対象名と知りたい内容を入力してください。')
        if aspect and self.flow_topic:
            topic=self.flow_topic
            choices=topic_choices(topic)
            if choices:
                self.flow_choice=dict(choices=choices,question=text,time=time.monotonic())
                return text,self.track(text,'「'+aspect+'」はどちらについてですか？\n'+'\n'.join(choices)+'\n対象名で答えてください。まだ再検索していません。')
            query=topic+' '+aspect
            if aspect in ('料金','価格','値段','社長'):query+=' 現在 公式'
            if selected:query=text.replace(phrase,query,1)
            self.flow_resolving=True
            try:answer=self.report(query)
            finally:
                self.flow_resolving=False;self.flow_topic=topic;self.flow_time=time.monotonic()
            return text,'前の話題「'+topic+'」の続きとして調べました。\n\n'+answer
        if re.fullmatch(r'(?:それ|そっち|あれ)(?:は|って)?',compact):
            return text,self.track(text,'「'+self.flow_topic+'」のどの点を知りたいですか？' if self.flow_topic else '「それ」が指す対象を教えてください。')
        # Let weather, earthquake and sources keep their existing specialized context.
        keep=SOURCE_REQUEST.fullmatch(re.sub(r'\s+','',compact)) or PRINCIPAL.fullmatch(phrase.strip()) or aspect
        if not keep and not school_subject(phrase):self.flow_topic=None
        return super().prepare_context(text)
