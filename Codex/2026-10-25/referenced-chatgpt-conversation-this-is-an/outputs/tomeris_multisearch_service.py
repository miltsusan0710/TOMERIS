"""Evidence-first reports: retrieved page excerpts only, no generated factual claims."""
from datetime import datetime,timezone,timedelta
import re
import unicodedata
from urllib.parse import urlsplit
from tomeris_site_search import DesktopService as SiteService,site_request,site_query
from tomeris_web_search import search_web,SearchError,needs_search,public_url
from tomeris_capabilities import research_requested,research_queries
from tomeris_weather_service import weather_request
from tomeris_weather_followup import region_reply
from tomeris_page_reader import fetch_page,PageError
from tomeris_strict_evidence import terms,passages,relevance_score
from tomeris_search_methods import SearchMethods,MethodError,wikipedia_page,search_topic
from tomeris_google_grounding import google_search,save_grounding


def needs_clarification(question):
    return bool(re.search(r'ジャービス|\bjarvis\b',question,re.I)) and not re.search(r'アイアンマン|マーベル|marvel|iron.?man|NVIDIA|製品名|会社名|github.com/',question,re.I)

class DesktopService(SiteService):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.pending_subject=False;self.methods=SearchMethods()
    def chat(self,text,model,use_memory=False):
        self.pending_subject=False
        return super().chat(text,model,use_memory)
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        arithmetic=self.arithmetic(question)
        if arithmetic is not None:
            self.pending_subject=False
            return arithmetic
        if self.pending_subject:
            if re.search(r'アイアンマン|マーベル|marvel|iron.?man',question,re.I):
                self.pending_subject=False
                return self.report('マーベル アイアンマン JARVIS ジャービス',progress,model)
            if re.fullmatch(r'(実在|実在する製品|製品|アプリ)[。！!？?]*',question):
                return self.track(question,'実在する製品の正式名称、提供元、または公式URLを教えてください。同名の別製品を混ぜないために確認しています。')
            self.pending_subject=False
        if weather_request(question) is not None or (self.pending_weather and region_reply(question)):
            return super().web_chat(question,model,use_memory,automatic,progress)
        if site_request(question) or research_requested(question) or re.search(r'https?://',question) or not automatic or needs_search(question):
            return self.report(question,progress,model)
        return super().web_chat(question,model,use_memory,automatic,progress)
    def research(self,question,model,progress=None):return self.report(question,progress,model)
    def sites(self,question,progress=None):return self.report(question,progress)
    def report(self,question,progress=None,model=None):
        self.pending_weather=None
        direct_urls=re.findall(r'https?://[^\s<>「」]+',question)[:3]
        if not direct_urls and needs_clarification(question):
            self.pending_subject=True
            return self.track(question,'どの「ジャービス」について調べますか？\n・アイアンマンに登場するAI\n・実在するAI製品や会社（正式名称・提供元を教えてください）\n対象を確認してから、本文と出典を調べます。')
        topic=question if direct_urls else (site_query(question) if site_request(question) else search_topic(question))
        if not topic:return self.track(question,'調べたいテーマや正式名称を入れてください。「そのサイト」だけでは対象を確定できません。')
        if len(topic)>(3000 if direct_urls else 180):return self.track(question,'調べるテーマを180文字以内で入力してください。')
        if self.demo:return self.track(question,'画面確認用：本文調査は実行していません。')
        wanted=terms(topic)
        if not wanted:return self.track(question,'調査対象の名前を特定できませんでした。URLだけでなく「Ollamaの機能」のように対象名も入力してください。')
        rows=[];seen=set();failures=[]
        for url in direct_urls:
            if public_url(url) and url not in seen:
                seen.add(url);rows.append(dict(title='指定されたページ',url=url,snippet=topic))
        for query in (() if direct_urls else (topic,)):
            if progress:progress('調査するページを検索しています：'+query)
            found,notes=self.methods.candidates(query)
            failures.extend(notes)
            for row in found:
                url=row.get('url','')
                if not public_url(url) or url in seen:continue
                seen.add(url);rows.append(row)
        rows.sort(key=lambda row:relevance_score(row.get('title','')+' '+row.get('snippet',''),wanted),reverse=True)
        checked=[];tried=0;hosts={};final_urls=set()
        for row in rows:
            if tried>=3:break
            host=urlsplit(row['url']).hostname
            if hosts.get(host,0)>=2:continue
            hosts[host]=hosts.get(host,0)+1;tried+=1
            if progress:progress(f'出典の本文を確認しています（{tried}/最大3ページ）…')
            try:
                page=wikipedia_page(row) if row.get('wiki_id') else fetch_page(row['url'])
                if page['url'] in final_urls:continue
                final_urls.add(page['url'])
                excerpt=passages(page,topic)
                if not excerpt:failures.append(row.get('title','ページ')+'：質問に関連する本文を抽出できませんでした。');continue
                checked.append(dict(page=page,excerpts=excerpt))
            except (PageError,MethodError) as exc:failures.append(row.get('title','ページ')+'：'+str(exc))
        stamp=datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M JST')
        header=f'調査対象：{topic}\n取得日時：{stamp}'
        if not checked:
            answer=header+'\n\n【結論】\n質問に答えるための本文根拠を取得できませんでした。検索の抜粋やAIの推測から結論を作っていません。'
        else:
            blocks=[]
            for i,item in enumerate(checked,1):
                page=item['page'];quotes='\n'.join('「'+text+'」' for text in item['excerpts'])
                date='掲載日（ページの記載）：'+page['published'] if page['published'] else '掲載日：確認できませんでした'
                if page.get('updated'):date='記事の更新日時（提供元の記載）：'+page['updated']
                if page.get('provider'):date+='\n資料種別：'+page['provider']
                blocks.append(f"[{i}] {page['title'] or 'ページ本文'}\n{quotes}\n{date}\n{page['url']}")
            answer=header+f'\n\n【対象語が含まれる本文・原文】\n{len(checked)}ページから対象語が含まれる記述を抽出しました。以下は出典に書かれた内容であり、事実として裏取り済みという意味ではありません。\n\n'+'\n\n'.join(blocks)
            domains={urlsplit(item['page']['url']).hostname for item in checked}
            answer+='\n\n【確認の範囲】\n自動要約は停止しています。対象語の一致と原文の取得を確認しただけで、記述の正確さ・最新性・公式性・質問への十分性を保証するものではありません。'
            if len(domains)<2:answer+='\n複数の提供元による照合はできていません。'
            answer+='\n最大3ページの範囲です。質問の全項目に答えられない場合があります。'
        if failures:answer+='\n\n【使用した方法・取得状況】\n'+'\n'.join(failures)
        if not checked:return self.track(question,answer)
        return self.save_answer(question,answer)

    def configure_methods(self,mode,brave_key,gemini_key,gemini_model):
        self.methods.configure(mode,brave_key,gemini_key,gemini_model)
        return '調査方法を変更しました。この起動中のみ有効です。APIキーはファイルに保存しません。'
    def google_grounded_report(self,question):
        if self.demo:raise MethodError('画面確認用モードではGoogle APIに接続しません。')
        value=google_search(question,self.methods.gemini_key,self.methods.gemini_model)
        return save_grounding(value,question,self.data_dir/'google_reports')
