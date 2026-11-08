import re
from tomeris_search_methods import brave_search
from tomeris_web_search import search_web,SearchError
from tomeris_search_methods import MethodError
from tomeris_conversation_preferences import DesktopService as BaseService
from tomeris_auto_research_v029 import AutoMethods as BaseMethods
from tomeris_source_catalogue import Catalogue
from tomeris_earthquake import recent_earthquake,fetch_latest,EarthquakeError,PAGE

class AutoMethods(BaseMethods):
    def candidates(self,text):
        fresh=bool(re.search(r'今の|今起き|現在|最新|速報|直近|さっき|今日|ニュース|運行|遅延',self.question_context or text))
        if self.mode=='自動' and fresh:
            name='Brave API' if self.brave_key else 'Bing RSS（試験）'
            try:rows=brave_search(text,self.brave_key) if self.brave_key else search_web(text)
            except (MethodError,SearchError) as exc:return [],['最新情報の検索：'+name+'／'+str(exc),'百科事典や保存資料への代替はしていません。']
            return rows,['最新情報の検索：'+name,'記事の更新日だけで出来事の発生日時を確認したとは扱いません。']
        rows,notes=super().candidates(text)
        if self.mode=='自動':
            known=self.catalogue.candidates(text)
            if known:
                urls={r['url'] for r in rows}
                rows.extend(r for r in known if r['url'] not in urls)
                notes.append('保存した出典も再取得候補に追加しました。保存時の本文を今回の回答に転用していません。')
        return rows,notes

class DesktopService(BaseService):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.catalogue=Catalogue(self.data_dir)
        self.methods=AutoMethods();self.methods.catalogue=self.catalogue
    def special(self,text):
        if text.strip() in ('学習した資料を見せて','学習状況を教えて'):return self.track(text,self.catalogue.summary())
        commands={'ネット学習を停止':False,'ネット学習を再開':True}
        if text.strip() in commands:
            self.catalogue.save(self.catalogue.rows,commands[text.strip()])
            return self.track(text,self.catalogue.summary())
        if text.strip()=='学習した資料を消去':
            self.catalogue.save([],self.catalogue.enabled)
            return self.track(text,'保存した調査資料を消去しました。通常の記憶・会話履歴は保持しています。')
        if recent_earthquake(text):
            self.pending_weather=None;self.last_research_request=None
            if self.demo:return self.track(text,'画面確認用：地震情報は取得していません。')
            try:answer=fetch_latest()
            except EarthquakeError as exc:answer='今の地震の震源は未確認です。\n'+str(exc)+'\n古い記事やAIの推測で補っていません。\n気象庁の最新情報：'+PAGE
            return self.track(text,answer)
        return None
    def chat(self,text,model,use_memory=False):
        answer=self.special(text)
        return answer if answer is not None else super().chat(text,model,use_memory)
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        answer=self.special(question)
        return answer if answer is not None else super().web_chat(question,model,use_memory,automatic,progress)
    def report(self,question,progress=None,model=None):
        answer=self.special(question)
        if answer is not None:return answer
        self.last_evidence_items=[]
        answer=super().report(question,progress,model)
        try:
            count=self.catalogue.learn(getattr(self,'last_evidence_items',[]))
            if count:answer+=f'\n\n出典つきの未検証資料を{count}件保存しました。次の関連調査で再取得候補に使います。'
        except (OSError,ValueError):answer+='\n\n資料学習への保存はできませんでした。調査結果は上記のとおりです。'
        return answer
