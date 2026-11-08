"""Site requests return retrieved links, never model-invented URLs."""
import re
import unicodedata
from urllib.parse import urlsplit,urlunsplit
from tomeris_weather_service import DesktopService as WeatherService
from tomeris_web_search import search_web,SearchError,public_url,clean


def site_request(text):
    return bool(re.search(r'(?:サイト|ウェブページ|ホームページ|URL|ＵＲＬ|リンク).{0,20}(?:出して|教えて|紹介|見せて|探して|挙げて|一覧|知りたい)|(?:関連サイト|公式サイト|参考サイト)(?:は|を|[？?]|$)',text,re.I))

def site_query(text):
    if re.match(r"^(その|この|それ|関連|公式|参考)(?:サイト|URL|リンク)",text,re.I): return None
    match=re.match(r'(.+?)(?:に関する|についての|の)?(?:ウェブサイト|サイト|ウェブページ|ホームページ|URL|ＵＲＬ|リンク)',text,re.I)
    topic=match[1].strip(' 「」『』') if match else ''
    topic=re.sub(r'(?:公式|関連|参考)$','',topic).strip()
    topic=re.sub(r'(?:に関する|についての|の)$','',topic).strip()
    if topic in ('関連','公式','参考','その','それ','この') or not topic:
        return None
    return topic

def normalized(text): return unicodedata.normalize('NFKC',text).casefold()

def retrieved_sites(rows,topic):
    result=[];seen=set()
    terms=[x for x in re.split(r'\s+',normalized(topic)) if x]
    for row in rows:
        url=row.get('url','')
        if not public_url(url):continue
        parsed=urlsplit(url)
        key=urlunsplit((parsed.scheme.lower(),parsed.netloc.lower(),parsed.path.rstrip('/'),parsed.query,''))
        if key in seen:continue
        title=clean(row.get('title',''));snippet=clean(row.get('snippet',''))
        evidence=normalized(title+' '+snippet)
        if terms and not any(term in evidence for term in terms):continue
        seen.add(key);result.append(dict(title=title,url=url,snippet=snippet))
        if len(result)==5:break
    return result

class DesktopService(WeatherService):
    def chat(self,text,model,use_memory=False):
        if site_request(text):
            self.pending_weather=None
            return self.track(text,'サイトのURLは検索して確認します。「会話＋自動検索」または「ネット検索」に切り替えて、同じ質問を送ってください。未確認のURLは作りません。')
        return super().chat(text,model,use_memory)
    def web_chat(self,question,model,use_memory=False,automatic=False,progress=None):
        if site_request(question):return self.sites(question,progress)
        return super().web_chat(question,model,use_memory,automatic,progress)
    def research(self,question,model,progress=None):
        if site_request(question):return self.sites(question,progress)
        return super().research(question,model,progress)
    def sites(self,question,progress=None):
        self.pending_weather=None
        topic=site_query(question)
        if not topic:return self.track(question,'何についてのサイトを探しますか？「ジャービスに関するサイトを出して」のように、テーマ名を入れてください。')
        if len(topic)>300:return self.track(question,'検索するテーマは300文字以内にしてください。')
        if progress:progress('サイトを検索しています：'+topic)
        if self.demo:return self.track(question,'画面確認用：サイト検索は実行していません。')
        try:rows=retrieved_sites(search_web(topic),topic)
        except SearchError as exc:return self.track(question,str(exc)+'\n確認できていないURLは表示しません。テーマ名を添えて再試行してください。')
        if not rows:return self.track(question,'「'+topic+'」について使える検索結果を取得できませんでした。\n対象の分野や正式名称を付けて、もう一度送ってください。未確認のURLは作りません。')
        blocks=[f"{i}. {r['title']}\n{r['url']}\n{r['snippet'][:300]}" for i,r in enumerate(rows,1)]
        answer='「'+topic+'」の検索結果です。\n\n'+'\n\n'.join(blocks)+'\n\n検索結果から取得したURLのみを表示しています。リンク先の本文・公式性は未確認です。同名の別の対象が含まれる場合は、分野や正式名称を指定してください。'
        return self.save_answer(question,answer)
