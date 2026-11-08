"""Question-scoped method selection. Explicit instructions never fall back."""
import re
import webbrowser
from tomeris_multisearch_service import DesktopService as BaseService
from tomeris_search_methods import SearchMethods, MethodError, browser_search_url, wikipedia_search

NAMES=r'Wikipedia英語|英語版Wikipedia|Wikipedia|ウィキペディア|Google|グーグル|Gemini|ジェミニ|Brave|ブレイブ|Bing|ビング|DuckDuckGo|ダックダックゴー'
MAP={'wikipedia英語':'Wikipedia（英語）','英語版wikipedia':'Wikipedia（英語）','wikipedia':'Wikipedia（日本語）','ウィキペディア':'Wikipedia（日本語）','google':'Google','グーグル':'Google','gemini':'Google API','ジェミニ':'Google API','brave':'Brave API','ブレイブ':'Brave API','bing':'Bing','ビング':'Bing','duckduckgo':'DuckDuckGo','ダックダックゴー':'DuckDuckGo'}

def instruction(text):
    # Only instruction boundaries count; a provider mentioned as a topic does not.
    start=re.match(r'^\s*('+NAMES+r')(?:だけ)?(?:で|を使って|を使い|から)[、,\s]*(.*)$',text,re.I)
    end=re.match(r'^(.*?)[を、,\s]*('+NAMES+r')(?:だけ)?(?:で|を使って)(?:調べて|検索して|調査して)(?:ください)?[。！!？?]*$',text,re.I)
    if start:return MAP[start[1].lower()],start[2].strip()
    if end:return MAP[end[2].lower()],end[1].strip()
    return None,text

class AutoMethods(SearchMethods):
    def __init__(self):super().__init__();self.mode='自動'
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
        broad=bool(re.search(r'最新|ニュース|価格|料金|発売|今日|現在|公式|サイト|比較|おすすめ',text))
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
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.methods=AutoMethods()
    def chat(self,text,model,use_memory=False):
        if instruction(text)[0]:return self.report(text,model=model)
        return super().chat(text,model,use_memory)
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        if instruction(question)[0]:return self.report(question,progress,model)
        return super().web_chat(question,model,use_memory,automatic,progress)
    def report(self,question,progress=None,model=None):
        selected,topic=instruction(question)
        if not selected:return super().report(question,progress,model)
        self.pending_weather=None;self.pending_subject=False
        if not topic:return self.track(question,'指定した方法で何を調べるか入力してください。例：Googleでアイアンマンについて調べて')
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
        finally:self.methods.mode=old
