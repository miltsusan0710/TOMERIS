"""Explicit topic reset and failed follow-up boundaries."""
import re
from tomeris_collection_settings import DesktopService as BaseService
class DesktopService(BaseService):
    def prepare_context(self,text):
        changed=re.fullmatch(r'(?:別の話(?:にして|をしよう|をしたい)?|話を変えて|話題を変えたい)[。！？!?]*',text.strip())
        prefix=re.match(r'^(?:別の話|話を変えて)[、,:：]\s*(.+)$',text.strip())
        if changed or prefix:
            self.clear_tool_context();self.session_turns=[]
            if changed:return text,self.track(text,'話題を切り替えました。次に話したいことを教えてください。')
            return super().prepare_context(prefix[1])
        return super().prepare_context(text)
    def continue_research(self,question,model=None,progress=None):
        # Do not leave the last successful research active after a failed continuation.
        self.last_evidence_urls=set()
        answer=super().continue_research(question,model,progress)
        if not self.last_evidence_urls:
            self.last_research_request=None;self.followup_seen_urls=set();self.research_source_snapshot=None
        return answer
