"""Re-fetch the previous overview for details, without reusing cached excerpts."""
import re
from tomeris_collection_rotation import DesktopService as BaseService
from tomeris_overview import overview_subject, key
from tomeris_name_punctuation import passages
from tomeris_auto_research_v029 import instruction

class DesktopService(BaseService):
    def continue_research(self,question,model=None,progress=None):
        method,phrase=instruction(question)
        previous=self.last_research_request
        subject=overview_subject(instruction(previous)[1]) if previous else None
        if not subject or not re.fullmatch(r'(?:もっと|さらに)?詳しく(?:教えて|調べて)?[。！？!?]*',phrase.strip()):
            return super().continue_research(question,model,progress)
        request=previous if not method else question.replace(phrase,instruction(previous)[1],1)
        seen=set(self.followup_seen_urls)
        self.followup_seen_urls=set()
        self._continuing=True
        self._detail_subject=subject
        try:
            result=self.report(request,progress,model)
            return '詳細の再調査：'+subject+'\n同じ記事も再取得し、見出し以降の記述を確認します。作品・時期が異なる記述は区別して読んでください。\n\n'+result
        finally:
            self._continuing=False
            self._detail_subject=None
            self.followup_seen_urls.update(seen)
            if not self.last_research_request:self.last_research_request=previous

    def extract_passages(self,page,topic):
        subject=getattr(self,'_detail_subject',None)
        if subject and page.get('provider','').startswith('Wikipedia') and key(page.get('title',''))==key(subject):
            parts=re.split(r'\n\s*==',page['text'],maxsplit=1)
            return passages(dict(page,text=parts[1]),topic) if len(parts)>1 else []
        return super().extract_passages(page,topic)
