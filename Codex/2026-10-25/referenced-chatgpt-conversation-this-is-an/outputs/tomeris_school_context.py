"""Carry a school into a bounded principal follow-up, never a generic biography."""
import re
from tomeris_school_location import DesktopService as BaseService,subject,SCHOOLS
from tomeris_auto_research_v029 import instruction

PRINCIPAL=re.compile(r'(?:その学校の|そこの|今の|現在の)?校長(?:先生)?(?:は|って|の名前は)(?:誰|だれ|何という人|何ていう人)(?:ですか|なの)?[？?。！!]*')

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.school_topic=None;self.pending_school_principal=False
    def clear_tool_context(self):
        self.school_topic=None
        self.pending_school_principal=False
        return super().clear_tool_context()
    def school_location(self,text,model=None,progress=None):
        _,phrase=instruction(text);name=subject(phrase)
        answer=super().school_location(text,model,progress)
        if name:self.school_topic=SCHOOLS.get(name,(name,None))[0]
        return answer
    def principal_followup(self,text,model=None,progress=None):
        selected,phrase=instruction(text)
        pending=self.pending_school_principal;self.pending_school_principal=False
        reply=re.fullmatch(r'([^\s「」]{1,60}(?:小学校|中学校|高校|高等学校|大学))(?:です)?[。！!]*',phrase.strip()) if pending else None
        if reply:self.school_topic=SCHOOLS.get(reply[1],(reply[1],None))[0]
        elif not PRINCIPAL.fullmatch(phrase.strip()):return None
        school=self.school_topic
        if not school:
            self.pending_school_principal=True
            return self.track(text,'どの学校の校長ですか？学校名を教えてください。')
        # Keep the request out of the generic WHO/person-definition path.
        query=school+' 現在の校長 公式'
        if selected:query=text.replace(phrase,query,1)
        try:
            result=self.report(query,progress,model)
            return '調査対象：'+school+'の校長\n氏名や在任時点を確認できない場合は、現在の校長とは断定しません。\n\n'+result
        finally:self.school_topic=school
    def prepare_context(self,text):
        answer=self.principal_followup(text)
        if answer is not None:return text,answer
        if not subject(instruction(text)[1]):self.school_topic=None
        return super().prepare_context(text)
    def chat(self,text,model,use_memory=False):
        answer=self.principal_followup(text,model)
        if answer is not None:return answer
        if not subject(instruction(text)[1]):self.school_topic=None
        return super().chat(text,model,use_memory)
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        answer=self.principal_followup(question,model,progress)
        if answer is not None:return answer
        if not subject(instruction(question)[1]):self.school_topic=None
        return super().web_chat(question,model,use_memory,automatic,progress)
