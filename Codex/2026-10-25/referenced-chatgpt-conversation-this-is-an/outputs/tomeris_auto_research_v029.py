"""Question-scoped method selection. Explicit instructions never fall back."""
import re
import webbrowser
from tomeris_page_reader import fetch_page, PageError
from tomeris_evidence_v029 import DesktopService as BaseService
from tomeris_search_methods import SearchMethods, MethodError, browser_search_url, wikipedia_search

NAMES=r'Wikipedia英語|英語版Wikipedia|Wikipedia|ウィキペディア|Google|グーグル|Gemini|ジェミニ|Brave|ブレイブ|Bing|ビング|DuckDuckGo|ダックダックゴー'
MAP={'wikipedia英語':'Wikipedia（英語）','英語版wikipedia':'Wikipedia（英語）','wikipedia':'Wikipedia（日本語）','ウィキペディア':'Wikipedia（日本語）','google':'Google','グーグル':'Google','gemini':'Google API','ジェミニ':'Google API','brave':'Brave API','ブレイブ':'Brave API','bing':'Bing','ビング':'Bing','duckduckgo':'DuckDuckGo','ダックダックゴー':'DuckDuckGo'}

def instruction(text):
    text=text.strip()
    if re.match(r'^('+NAMES+r')で(?:できる|何ができる|使える)',text,re.I):return None,text
    if re.search(r'('+NAMES+r')(?:と|・|、|及び)('+NAMES+r')(?:だけ)?で',text,re.I):return '要確認',text
    # Do not interpret negation or conflicting provider instructions as permission to use the first provider.
    if re.search(r'('+NAMES+r')(?:で(?:は)?なく|以外|を使わず|を使わない)',text,re.I):
        return '要確認',text
    directive=r'('+NAMES+r')(?:だけ)?(?:で(?!き)|を使って|を使い|から)'
    found=list(re.finditer(directive,text,re.I))
    if len({MAP[m[1].lower()] for m in found})>1:return '要確認',text
    start=re.match(r'^'+directive+r'[、,\s]*(.*)$',text,re.I)
    end=re.match(r'^(.*?)[を、,\s]*('+NAMES+r')(?:だけ)?(?:で|を使って)(?:調べて|検索して|調査して)(?:ください)?[。！!？?]*$',text,re.I)
    if start:return MAP[start[1].lower()],start[2].strip()
    if end:return MAP[end[2].lower()],end[1].strip()
    return None,text


def missing_topic(text):
    return not text or bool(re.fullmatch(r'(?:検索|調査|調べて|検索して|調査して|探して)(?:ください)?[。！!？?]*',text))

class AutoMethods(SearchMethods):
    def __init__(self):super().__init__();self.mode='自動';self.question_context=''
    def configure(self,mode,*args,**kwargs):
        super().configure('Wikipedia（日本語）' if mode=='自動' else mode,*args,**kwargs)
        self.mode=mode
    def candidates(self,text):
        if self.mode=='Wikipedia（英語）':
            try:return wikipedia_search(text,'en'),['指定方法：Wikipedia英語']
            except MethodError as exc:return [],['Wikipedia英語：'+str(exc)]
        if self.mode!='自動':return super().candidates(text)
        original=self.mode
        # Broad/current queries use general web search; encyclopedia topics use Wikipedia first.
        broad=bool(re.search(r'最新|ニュース|価格|料金|発売|今日|現在|公式|サイト|比較|おすすめ',self.question_context or text))
        chosen=('Brave API' if self.brave_key else 'Bing RSS（試験）') if broad else 'Wikipedia（日本語）'
        notes=['自動選択：'+chosen+('（一般Web・最新情報の質問）' if broad else '（対象の概要・資料の検索）')]
        try:
            self.mode=chosen;rows,info=super().candidates(text);notes.extend(info)
            if not rows:
                fallback=('Brave API' if self.brave_key else 'Bing RSS（試験）') if chosen=='Wikipedia（日本語）' else 'Wikipedia（日本語）'
                self.mode=fallback;notes.append('候補なしのため追加検索：'+fallback)
                rows,info=super().candidates(text);notes.extend(info)
            return rows,notes
        finally:self.mode=original

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.methods=AutoMethods();self.pending_method=None
    def chat(self,text,model,use_memory=False):
        if instruction(text)[0] or self.pending_method:return self.report(text,model=model)
        return super().chat(text,model,use_memory)
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        if instruction(question)[0] or self.pending_method:return self.report(question,progress,model)
        return super().web_chat(question,model,use_memory,automatic,progress)
    def report(self,question,progress=None,model=None):
        selected,topic=instruction(question)
        if question.strip() in ('キャンセル','やめる','中止'):
            self.pending_method=None;self.pending_subject=False
            return self.track(question,'調査の確認待ちを取り消しました。')
        if selected=='要確認':
            self.pending_method=None
            return self.track(question,'調査方法を一つ指定してください。例：Wikipediaでアイアンマンについて調べて。今回は外部へ送信していません。')
        if not selected and self.pending_method:
            selected=self.pending_method;self.pending_method=None
        if not selected and re.fullmatch(r'https?://[^\s<>「」]+',question.strip()):
            return self.read_direct_url(question.strip())
        if not selected:
            old_context=self.methods.question_context
            try:
                self.methods.question_context=question
                return super().report(question,progress,model)
            finally:self.methods.question_context=old_context
        if self.pending_subject and re.search(r'アイアンマン|マーベル|marvel|iron.?man',topic,re.I):
            topic='マーベル アイアンマン JARVIS ジャービス'
        self.pending_weather=None;self.pending_subject=False
        if missing_topic(topic):
            self.pending_method=selected
            return self.track(question,'指定方法：'+selected+'。何を調べますか？次の入力をこの方法で調べます。取り消す場合は「キャンセル」と入力してください。')
        self.pending_method=None
        if selected.startswith('Wikipedia') and re.search(r'https?://',topic):
            return self.track(question,'Wikipediaで検索する対象名を入力してください。URL本文を直接読む場合は、方法の指定を外してURLを送ってください。')
        if self.demo:return self.track(question,'画面確認用：指定方法 '+selected+'。外部への検索は実行していません。')
        if selected in ('Google','Google API','Bing','DuckDuckGo'):
            try:
                if selected=='Google API' or (selected=='Google' and self.methods.gemini_key):
                    path=self.google_grounded_report(topic)
                    opened=webbrowser.open(path.resolve().as_uri())
                    answer='指定方法：Google検索付きGemini API\n報告を保存しました：'+str(path)+'\n'+('ブラウザーに表示しました。' if opened else 'ブラウザーを開けませんでした。保存先から開いてください。')
                else:
                    url=browser_search_url(selected,topic);opened=webbrowser.open(url)
                    answer='指定方法：'+selected+'\n'+('検索画面をブラウザーで開きました。' if opened else 'ブラウザーを開けませんでした。')+'\n'+url+'\n検索結果は自動取得していません。調べたいページのURLを送ると本文を確認します。'
                return self.track(question,answer)
            except (MethodError,OSError,webbrowser.Error) as exc:return self.track(question,'指定方法：'+selected+'\n実行できませんでした：'+str(exc)+'\n別の方法への切り替えはしていません。')
        old=self.methods.mode
        try:
            self.methods.mode=selected
            return super().report(topic,progress,model)
        finally:
            self.methods.mode=old
            if self.pending_subject:self.pending_method=selected

    def read_direct_url(self,url):
        self.pending_weather=None;self.pending_subject=False
        if self.demo:return self.track(url,'画面確認用：指定URLの本文は取得していません。')
        try:page=fetch_page(url)
        except PageError as exc:return self.track(url,'指定URLの本文を取得できませんでした。\n'+str(exc))
        excerpt=page['text'].strip()[:1800]
        if not excerpt:return self.track(url,'指定URLから本文を取得できませんでした。')
        answer='指定URLの本文（冒頭・最大1800文字）\n'+page.get('title','')+'\n'+page['url']+'\n\n'+excerpt+'\n\n本文を取得した結果です。事実確認や質問への回答はまだ行っていません。詳しく確認したい点を、対象名とURLを添えて入力してください。'
        return self.save_answer(url,answer)


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
        pending=self.pending_method
        answer=super().report(question,progress,model)
        if self.last_evidence_urls:
            prefixes={'Wikipedia（日本語）':'Wikipedia','Wikipedia（英語）':'Wikipedia英語','Brave API':'Brave'}
            self.last_research_request=(prefixes[pending]+'で'+question) if pending in prefixes and not instruction(question)[0] else question
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
            return '追加調査：'+topic+'\n表示済みの出典は除いて調べます。\n\n'+result
        finally:
            self._continuing=False
            if not self.last_research_request:self.last_research_request=previous
