"""Show only the sources actually read in the immediately preceding research."""
import re
from datetime import datetime,timezone,timedelta
from tomeris_tomorrow_plans import DesktopService as BaseService
from tomeris_web_search import public_url

SOURCE_REQUEST=re.compile(r'(?:その|さっきの|先ほどの|今の|この回答の)?(?:出典|情報源|根拠のサイト)(?:は|はどこ|はどこですか|を教えて|を教えてください|を見せて)?')

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.research_source_snapshot=None
    def clear_tool_context(self):
        super().clear_tool_context();self.research_source_snapshot=None
    def prepare_context(self,text):
        compact=re.sub(r'\s+','',text).rstrip('？?。！!')
        if SOURCE_REQUEST.fullmatch(compact):
            record=self.research_source_snapshot
            if not record:
                return text,self.track(text,'直前の調査で本文を取得した出典は確認できません。調べたい内容を指定してください。出典を推測して補いません。')
            lines=['直前の調査で本文を取得した出典です。','調査対象：'+record['question'],'取得時刻：'+record['time']]
            for i,source in enumerate(record['sources'],1):lines.extend([f"[{i}] {source['title']}",source['url']])
            lines.append('今回は再取得していません。出典の存在や原文の取得は、内容の正確さ・最新性の保証ではありません。')
            return text,self.track(text,'\n'.join(lines))
        # Keep this source list only across direct source questions, not unrelated turns.
        self.research_source_snapshot=None
        return super().prepare_context(text)
    def report(self,question,progress=None,model=None):
        self.research_source_snapshot=None;self.last_evidence_items=[]
        answer=super().report(question,progress,model)
        sources=[];seen=set()
        for item in getattr(self,'last_evidence_items',[]):
            page=item.get('page',{});url=page.get('url','')
            if not isinstance(url,str) or not public_url(url) or url in seen:continue
            if not item.get('excerpts'):continue
            seen.add(url);sources.append(dict(title=str(page.get('title','資料'))[:300],url=url))
        if sources:
            self.research_source_snapshot=dict(question=question,time=datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M JST'),sources=sources)
        return answer
