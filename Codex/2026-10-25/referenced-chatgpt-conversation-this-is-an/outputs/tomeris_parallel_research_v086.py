"""Independent search jobs; concise extractive summaries with source references."""
from concurrent.futures import ThreadPoolExecutor
import re
from tomeris_research_router import DesktopService as BaseService
from tomeris_search_methods import search_topic,wikipedia_search,brave_search
from tomeris_web_search import search_web,public_url
from tomeris_overview_resolution import resolve_title
from tomeris_overview import overview_subject,key

def overview_excerpts(page,subject):
    pattern=re.compile(re.escape(key(subject))+r'(?:（[^）]*）|\([^)]*\))*?(?:とは|は)')
    chosen=[]
    for sentence in re.split(r'(?<=[。！？])\s*|(?<=[.!?])\s+|\n+',page['text']):
        sentence=sentence.strip()
        if (20<=len(sentence)<=350 and pattern.search(key(sentence))
                and not re.search(r'トップ\s*>|HOME\s*>|閉鎖|メンテナンス|お問い合わせ|学習しましょう|解説します',sentence,re.I)):
            chosen.append(sentence)
        if len(chosen)==2:break
    return chosen

class ParallelMethods:
    def __init__(self, base):object.__setattr__(self,'_base',base)
    def __getattr__(self,name):return getattr(self._base,name)
    def __setattr__(self,name,value):setattr(self._base,name,value)
    def candidates(self,text):
        if self.mode!='自動':return self._base.candidates(text)
        query=search_topic(text);subject=overview_subject(self.question_context)
        self.resolved=None
        volatile=bool(re.search(r'現在|最新|今日|明日|ニュース|料金|価格|学費|入試|社長|学長',self.question_context or query))
        def wiki():
            row=resolve_title(subject) if subject else None
            if row:return [row],row
            rows=wikipedia_search(query)
            if subject:rows=[r for r in rows if key(r['title'])==key(subject)]
            return rows,None
        jobs=[('一般Web（Bing RSS・試験）',lambda:(search_web(query),None))]
        if not volatile:jobs.insert(0,('Wikipedia（対象記事）',wiki))
        else:jobs.append(('一般Web（公式情報の検索語）',lambda:(search_web(query+' 公式'),None)))
        if self.brave_key:
            token=self.brave_key
            jobs.append(('Brave API',lambda:(brave_search(query,token),None)))
        rows=[];notes=[];seen=set()
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures=[pool.submit(fn) for _,fn in jobs]
            for (name,_),future in zip(jobs,futures):
                try:
                    found,resolved=future.result()
                    if resolved:self.resolved=resolved
                    notes.append(name+'：'+str(len(found))+'候補')
                    for row in found:
                        url=row.get('url','')
                        if public_url(url) and url not in seen:seen.add(url);rows.append(row)
                except (ValueError,OSError):notes.append(name+'：取得失敗（他の方法は継続）')
        return rows,['並行検索：'+str(len(jobs))+'経路。候補の件数は正確性の点数ではありません。']+notes

def concise_report(answer,items):
    if not items:return answer
    bullets=[];sources=[];seen=set()
    for item in items:
        page=item['page']
        valid=[q for q in item['excerpts'] if q in page['text'] and key(q) not in seen]
        if not valid:continue
        quote=valid[0];seen.add(key(quote));number=len(sources)+1
        bullets.append(f'・{quote} [{number}]')
        date=page.get('updated') or page.get('published') or '不明'
        sources.append(f"[{number}] {page.get('title','資料')}\n{page['url']}\n資料の更新・掲載日時：{date}")
    if not bullets:return answer
    header=answer.split('\n\n',1)[0]
    methods=answer.split('【使用した方法・取得状況】',1)
    result=header+'\n\n【要点（取得本文から抜粋）】\n'+'\n'.join(bullets)
    result+='\n\n【出典】\n'+'\n\n'.join(sources)
    result+='\n\n【確認範囲】\n原文の重要箇所を短くまとめた抜粋です。出典間の一致・矛盾や内容の正しさは自動判定していません。'
    if len(sources)==1:result+='本文根拠を得られた出典は1件で、複数出典の照合には至っていません。'
    if len(methods)>1:result+='\n\n【検索状況】'+methods[1]
    return result

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.methods=ParallelMethods(self.methods)
    def extract_passages(self,page,topic):
        subject=overview_subject(self.methods.question_context)
        if subject and not getattr(self,'_detail_subject',None):
            resolved=self.methods.resolved
            if resolved and page.get('title')==resolved['title']:
                return super().extract_passages(page,topic)
            return overview_excerpts(page,subject)
        return super().extract_passages(page,topic)
    def save_answer(self,question,answer):
        if answer.startswith('調査対象：') and getattr(self,'last_evidence_items',None):
            answer=concise_report(answer,self.last_evidence_items)
        return super().save_answer(question,answer)
