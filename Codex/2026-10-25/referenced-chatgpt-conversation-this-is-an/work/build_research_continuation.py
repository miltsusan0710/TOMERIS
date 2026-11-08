from pathlib import Path
p=Path('outputs/tomeris_multisearch_service.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace('        self.pending_weather=None\n        direct_urls=',"        self.last_evidence_urls=set()\n        excluded=getattr(self,'followup_seen_urls',set())\n        self.pending_weather=None\n        direct_urls=",1)
s=s.replace("        for row in rows:\n            if tried>=3", "        for row in rows:\n            if row['url'] in excluded:continue\n            if tried>=3")
s=s.replace("                if page['url'] in final_urls:continue", "                if page['url'] in final_urls or page['url'] in excluded:continue")
s=s.replace("                checked.append(dict(page=page,excerpts=excerpt))", "                checked.append(dict(page=page,excerpts=excerpt))\n                self.last_evidence_urls.update((row['url'],page['url']))")
s=s.replace("answer=header+'\\n\\n【結論】\\n質問に答えるための本文根拠を取得できませんでした。検索の抜粋やAIの推測から結論を作っていません。'", "answer=header+'\\n\\n【結論】\\n'+('表示済みの資料以外から、追加の本文根拠を取得できませんでした。' if excluded else '質問に答えるための本文根拠を取得できませんでした。')+'検索の抜粋やAIの推測から結論を作っていません。'")
Path('outputs/tomeris_evidence_v029.py').write_text(s,encoding='utf-8')
s=Path('outputs/tomeris_auto_research_v0281.py').read_text(encoding='utf-8').replace('from tomeris_multisearch_service import','from tomeris_evidence_v029 import')
s+='''

RoutingService=DesktopService

def more_information(text):
    return bool(re.fullmatch(r'(?:他の情報(?:は|も)?|ほかの情報(?:は|も)?|他には|ほかには|他にも|もっと詳しく|さらに詳しく|詳しく|追加(?:の)?情報(?:は|も)?|続きを(?:調べて|教えて)|もっと教えて)(?:教えて|調べて)?[？?。！!]*',text.strip()))

class DesktopService(RoutingService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.last_research_request=None;self.followup_seen_urls=set();self.last_evidence_urls=set();self._continuing=False
    def is_followup(self,text):return more_information(instruction(text)[1])
    def chat(self,text,model,use_memory=False):
        if self.is_followup(text):return self.continue_research(text,model)
        self.last_research_request=None
        return super().chat(text,model,use_memory)
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        if self.is_followup(question):return self.continue_research(question,model,progress)
        self.last_research_request=None
        return super().web_chat(question,model,use_memory,automatic,progress)
    def report(self,question,progress=None,model=None):
        if self.is_followup(question):return self.continue_research(question,model,progress)
        if not self._continuing:
            self.followup_seen_urls=set();self.last_research_request=None
        self.last_evidence_urls=set()
        answer=super().report(question,progress,model)
        if self.last_evidence_urls:
            self.last_research_request=question
            self.followup_seen_urls.update(self.last_evidence_urls)
        return answer
    def continue_research(self,question,model=None,progress=None):
        previous=self.last_research_request
        if not previous:return self.track(question,'追加で調べる対象を教えてください。例：「アイアンマンについて調べて」。起動中に本文を取得した直前の調査がある場合は、「他の情報は？」で続けられます。')
        method,_=instruction(question)
        _,topic=instruction(previous)
        request=previous
        if method:
            # Keep the user's exact method spelling; replace only the follow-up phrase.
            request=question.replace(instruction(question)[1],topic,1)
        self._continuing=True
        try:
            result=self.report(request,progress,model)
            return '追加調査：'+topic+'\\n表示済みの出典は除いて調べます。\\n\\n'+result
        finally:
            self._continuing=False
            if not self.last_research_request:self.last_research_request=previous
'''
Path('outputs/tomeris_auto_research_v029.py').write_text(s,encoding='utf-8')
s=Path('outputs/tomeris_desktop_v0281.py').read_text(encoding='utf-8').replace('tomeris_auto_research_v0281','tomeris_auto_research_v029').replace('v0.28.1','v0.29')
Path('outputs/tomeris_desktop_v029.py').write_text(s,encoding='utf-8')
