"""Explicit search providers; keys are supplied in memory, never persisted."""
import json
import re
from html import unescape
from urllib.parse import urlencode,quote,urlsplit
from urllib.request import Request,build_opener,HTTPRedirectHandler,ProxyHandler
from urllib.error import HTTPError,URLError
from tomeris_web_search import search_web,SearchError,public_url,clean

class MethodError(ValueError):pass
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise MethodError('APIからの転送を拒否しました。')

def json_request(url,headers=None,payload=None,timeout=20):
    body=None if payload is None else json.dumps(payload,ensure_ascii=False).encode('utf-8')
    request=Request(url,data=body,headers={'User-Agent':'Tomeris/0.27 (local desktop research tool)','Accept':'application/json','Accept-Encoding':'identity',**({'Content-Type':'application/json'} if body else {}),**(headers or {})})
    try:
        with build_opener(ProxyHandler({}),NoRedirect()).open(request,timeout=timeout) as response:
            raw=response.read(2000001)
        if len(raw)>2000000:raise MethodError('API応答が大きすぎます。')
        value=json.loads(raw)
        if not isinstance(value,dict) or value.get('error'):raise MethodError('APIの応答形式を確認できませんでした。')
        return value
    except HTTPError as exc:
        code=exc.code;exc.close()
        message={401:'APIキーを確認してください。',403:'利用権限・APIキーを確認してください。',429:'利用枠または回数制限に達しました。',404:'APIまたはモデル名を確認してください。'}.get(code,'時間をおいて再試行してください。')
        raise MethodError(f'HTTP {code}：{message}') from None
    except (URLError,OSError,TimeoutError):raise MethodError('通信できませんでした。接続状態を確認してください。') from None
    except (json.JSONDecodeError,UnicodeError):raise MethodError('API応答を読み取れませんでした。') from None

def search_topic(text):
    text=re.sub(r'^(?:調査|情報収集)\s*[:：]\s*','',text.strip())
    text=re.sub(r'(?:について|に関して)?(?:詳しく)?(?:調べて|教えて|調査して|情報収集して|報告して)(?:ください)?[。！？!?]*$','',text).strip()
    text=re.sub(r'(?:に関する|の)?(?:ウェブサイト|サイト|URL|リンク)(?:を)?(?:出して|教えて|紹介して|見せて|探して|挙げて)(?:ください)?[。！？!?]*$','',text,flags=re.I).strip()
    if not text or len(text)>300:raise MethodError('検索するテーマを1〜300文字で入力してください。')
    return text

def wikipedia_search(query,language='ja'):
    if language not in ('ja','en'):raise MethodError('未対応の言語です。')
    data=json_request(f'https://{language}.wikipedia.org/w/api.php?'+urlencode(dict(action='query',list='search',srsearch=query,srlimit=5,format='json',utf8=1)))
    result=[]
    group=data.get('query',{})
    if not isinstance(group,dict) or not isinstance(group.get('search'),list):raise MethodError('Wikipedia検索の形式を確認できません。')
    for row in group['search']:
        if not isinstance(row,dict) or type(row.get('pageid')) is not int or not isinstance(row.get('title'),str):continue
        result.append(dict(title=row['title'],url=f'https://{language}.wikipedia.org/wiki/'+quote(row['title'].replace(' ','_'),safe=''),snippet=clean(row.get('snippet','')),provider='Wikipedia '+language,wiki_id=row['pageid'],wiki_lang=language))
    return result

def wikipedia_page(row):
    language=row.get('wiki_lang');pageid=row.get('wiki_id')
    if language not in ('ja','en') or type(pageid) is not int or pageid<=0:raise MethodError('Wikipediaの記事IDを確認できません。')
    data=json_request(f'https://{language}.wikipedia.org/w/api.php?'+urlencode(dict(action='query',prop='extracts|info|revisions',pageids=pageid,explaintext=1,inprop='url',rvprop='timestamp',format='json',formatversion=2,utf8=1)))
    pages=data.get('query',{}).get('pages',[])
    if not isinstance(pages,list) or len(pages)!=1:raise MethodError('記事を取得できませんでした。')
    page=pages[0];text=page.get('extract','');url=page.get('fullurl','')
    if not isinstance(text,str) or len(text.strip())<40 or not public_url(url) or urlsplit(url).hostname!=f'{language}.wikipedia.org':raise MethodError('記事の本文・URLを確認できませんでした。')
    revised=page.get('revisions') or []
    updated=revised[0].get('timestamp','') if isinstance(revised,list) and revised and isinstance(revised[0],dict) else ''
    return dict(title=page.get('title','Wikipedia'),url=url,text=text[:50000],published='',updated=updated,provider='Wikipedia（二次資料）')

def brave_search(query,key):
    if not key:raise MethodError('Brave APIキー未設定です。')
    data=json_request('https://api.search.brave.com/res/v1/web/search?'+urlencode(dict(q=query,count=5,country='JP',search_lang='jp')),headers={'X-Subscription-Token':key})
    result=[]
    group=data.get('web',{})
    if not isinstance(group,dict) or not isinstance(group.get('results'),list):raise MethodError('Brave検索の形式を確認できません。')
    for row in group['results']:
        if isinstance(row,dict) and public_url(row.get('url','')):
            result.append(dict(title=clean(row.get('title','')),url=row['url'],snippet=clean(row.get('description','')),provider='Brave Search'))
    return result

def browser_search_url(engine,query):
    if not isinstance(query,str) or not query.strip() or len(query)>1000:raise MethodError('検索する文章を1〜1000文字で入力してください。')
    bases={'Google':'https://www.google.com/search','Bing':'https://www.bing.com/search','DuckDuckGo':'https://duckduckgo.com/'}
    if engine not in bases:raise MethodError('検索先を確認してください。')
    return bases[engine]+'?'+urlencode({'q':query.strip()})

class SearchMethods:
    def __init__(self):
        self.mode='Wikipedia（日本語）';self.brave_key='';self.gemini_key='';self.gemini_model='gemini-3.8-flash';self.status={}
    def configure(self,mode,brave_key='',gemini_key='',gemini_model='gemini-3.8-flash'):
        if mode not in ('Wikipedia（日本語）','Wikipedia（日英）','Brave API','併用（Wikipedia＋Brave）','Bing RSS（試験）'):raise MethodError('調査方法を選択してください。')
        for key in (brave_key,gemini_key):
            if key and (len(key)>500 or not key.isascii() or any(c.isspace() for c in key)):raise MethodError('APIキーの形式を確認してください。')
        if not re.fullmatch(r'gemini-[A-Za-z0-9._-]+',gemini_model):raise MethodError('GeminiのモデルIDを確認してください。')
        self.mode=mode;self.brave_key=brave_key;self.gemini_key=gemini_key;self.gemini_model=gemini_model
    def candidates(self,text):
        query=search_topic(text);rows=[];notes=[]
        methods=[]
        if 'Wikipedia' in self.mode:methods.append(('Wikipedia日本語',lambda:wikipedia_search(query,'ja')))
        if self.mode=='Wikipedia（日英）':
            english=query.replace('アイアンマン','Iron Man').replace('ジャービス','JARVIS').replace('マーベル','Marvel')
            methods.append(('Wikipedia英語',lambda:wikipedia_search(english,'en')))
        if 'Brave' in self.mode:methods.append(('Brave API',lambda:brave_search(query,self.brave_key)))
        if self.mode=='Bing RSS（試験）':methods.append(('Bing RSS（試験）',lambda:search_web(query)))
        for name,call in methods:
            try:
                found=call();rows.extend(found);note=f'{name}：{len(found)}件取得（内容の正確さは未検証）'
            except (MethodError,SearchError) as exc:note=f'{name}：{exc}'
            self.status[name]=note;notes.append(note)
        seen=set();unique=[]
        for row in rows:
            if row['url'] not in seen:seen.add(row['url']);unique.append(row)
        return unique,notes
