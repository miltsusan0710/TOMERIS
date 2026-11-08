"""Resolve verified school aliases before overview matching, without fuzzy guessing."""
from tomeris_topic_flow import DesktopService as BaseService
from tomeris_school_location import SCHOOLS
from tomeris_overview import overview_subject
from tomeris_auto_research_v029 import instruction

class DesktopService(BaseService):
    def report(self,question,progress=None,model=None):
        method,phrase=instruction(question)
        subject=overview_subject(phrase)
        if method is None and self.methods.mode=='自動' and subject in SCHOOLS:
            canonical=SCHOOLS[subject][0]
            if canonical!=subject:
                question=phrase.replace(subject,canonical,1)
                result=super().report(question,progress,model)
                self.school_topic=canonical
                return '「'+subject+'」を正式名称「'+canonical+'」として調べました。\n\n'+result
        result=super().report(question,progress,model)
        if subject in SCHOOLS:self.school_topic=SCHOOLS[subject][0]
        return result
