"""Recent JMA bulletins only; never substitute historical encyclopedia entries."""
from datetime import datetime,timezone,timedelta
from urllib.request import Request,build_opener,HTTPRedirectHandler,ProxyHandler
from urllib.parse import urlsplit
from urllib.error import URLError
import xml.etree.ElementTree as ET
import re
JST=timezone(timedelta(hours=9))
FEED='https://www.data.jma.go.jp/developer/xml/feed/eqvol.xml'
PAGE='https://www.jma.go.jp/bosai/map.html#contents=earthquake_map'
class EarthquakeError(ValueError):pass
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise EarthquakeError('転送先の情報は使用しません。')
def read_xml(url):
    p=urlsplit(url)
    if p.scheme!='https' or p.netloc!='www.data.jma.go.jp' or not p.path.startswith('/developer/xml/') or p.query or p.fragment:raise EarthquakeError('気象庁の電文URLを確認できません。')
    try:
        with build_opener(ProxyHandler({}),NoRedirect()).open(Request(url,headers={'User-Agent':'Tomeris/0.33'}),timeout=12) as response:raw=response.read(1500001)
        if len(raw)>1500000 or b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():raise EarthquakeError('電文の形式を確認できません。')
        return ET.fromstring(raw)
    except (URLError,OSError,ET.ParseError) as exc:raise EarthquakeError('気象庁の発表を取得できませんでした。') from exc

def value(node,path):return node.findtext('/'.join('{*}'+part for part in path.split('/')),'').strip()
def dt(text):
    try:
        result=datetime.fromisoformat(text.replace('Z','+00:00'))
        if result.tzinfo is None:raise ValueError()
        return result
    except ValueError:raise EarthquakeError('発生・発表時刻を確認できません。') from None

def recent_earthquake(text):
    if not re.search('地震|震源|揺れ|震度|津波',text):return False
    if re.search(r'今|さっき|先ほど|直近|最新|速報|今日',text):return True
    return bool(re.fullmatch(r'(?:地震の)?(?:震源|震度)(?:は|を教えて)?[？?。]*',text.strip()))

def fetch_latest(now=None):
    now=now or datetime.now(JST)
    root=read_xml(FEED)
    updated=dt(value(root,'updated'))
    if not -120<=(now-updated).total_seconds()<=600:raise EarthquakeError('配信一覧が古いか、時刻を確認できません。')
    entries=[]
    for entry in root.findall('{*}entry'):
        if value(entry,'title') not in ('震度速報','震源に関する情報','震源・震度に関する情報','震源・震度情報'):continue
        stamp=dt(value(entry,'updated'))
        link=entry.find('{*}link')
        if link is not None:entries.append((stamp,link.get('href','')))
    if not entries:raise EarthquakeError('取得した一覧に直近の地震電文がありません。地震がなかったという意味ではありません。')
    _,url=max(entries,key=lambda x:x[0])
    report=read_xml(url)
    if value(report,'Control/Status')!='通常' or value(report,'Head/InfoType') not in ('発表','訂正'):raise EarthquakeError('最新の電文が訓練・取消などのため、震源を確定しません。')
    published=dt(value(report,'Head/ReportDateTime'))
    origin=value(report,'Body/Earthquake/OriginTime') or value(report,'Head/TargetDateTime')
    occurred=dt(origin)
    if not -120<=(now-published).total_seconds()<=900 or not -120<=(now-occurred).total_seconds()<=900:raise EarthquakeError('取得した発表は直近15分の地震と確認できません。過去の地震を「今の地震」として表示しません。')
    place=value(report,'Body/Earthquake/Hypocenter/Area/Name')
    title=value(report,'Control/Title')
    answer='気象庁の直近の発表：'+title+'\n対象時刻：'+occurred.astimezone(JST).strftime('%Y-%m-%d %H:%M:%S JST')+'\n発表時刻：'+published.astimezone(JST).strftime('%Y-%m-%d %H:%M:%S JST')
    if place:answer+='\n震源地：'+place
    else:answer+='\n震源地：この発表では未確認です。震度速報を震源の確定情報として扱いません。'
    answer+='\n\nあなたが感じた揺れと同じ地震かは特定できません。津波情報・避難の要否はこの表示から判断できません。気象庁の最新情報を確認してください。\n'+PAGE+'\n出典電文：'+url+'\n取得：'+now.astimezone(JST).strftime('%Y-%m-%d %H:%M:%S JST')
    return answer
