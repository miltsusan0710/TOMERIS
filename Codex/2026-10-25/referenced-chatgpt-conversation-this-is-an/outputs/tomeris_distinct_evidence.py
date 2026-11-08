"""Do not count identical excerpts from several URLs as new evidence."""
import re
import unicodedata
from tomeris_detail_followup import DesktopService as BaseService

class DesktopService(BaseService):
    def report(self,question,progress=None,model=None):
        previous=getattr(self,'_seen_excerpts',None)
        old_count=getattr(self,'_duplicate_count',0)
        self._seen_excerpts=set()
        self._duplicate_count=0
        try:
            answer=super().report(question,progress,model)
            if self._duplicate_count:answer+='\n\n重複した原文は追加の根拠として数えていません。別の文章であっても出典の独立性を保証するものではありません。'
            return answer
        finally:self._seen_excerpts=previous;self._duplicate_count=old_count

    def extract_passages(self,page,topic):
        excerpts=super().extract_passages(page,topic)
        seen=getattr(self,'_seen_excerpts',None)
        if seen is None:return excerpts
        unique=[]
        for excerpt in excerpts:
            fingerprint=re.sub(r'\s+','',unicodedata.normalize('NFKC',excerpt))
            if fingerprint not in seen:
                unique.append(excerpt);seen.add(fingerprint)
            else:self._duplicate_count+=1
        return unique
