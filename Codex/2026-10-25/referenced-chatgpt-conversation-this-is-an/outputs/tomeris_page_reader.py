"""Bounded public-page reader: pinned public IP, validated redirects, no JS/auth."""
from html.parser import HTMLParser
import http.client
import ipaddress
import re
import socket
import ssl
import time
from urllib.parse import urlsplit,urljoin,urlunsplit

class PageError(ValueError):pass

class PublicHTTPS(http.client.HTTPSConnection):
    def __init__(self,host,address,timeout):
        super().__init__(host,timeout=timeout,context=ssl.create_default_context());self.address=address
    def connect(self):
        sock=socket.create_connection((self.address,443),self.timeout)
        try:self.sock=self._context.wrap_socket(sock,server_hostname=self.host)
        except BaseException:sock.close();raise

class PublicHTTP(http.client.HTTPConnection):
    def __init__(self,host,address,timeout):super().__init__(host,timeout=timeout);self.address=address
    def connect(self):self.sock=socket.create_connection((self.address,80),self.timeout)

def target(url):
    try:p=urlsplit(url);port=p.port
    except ValueError:raise PageError('URLの形式が不正です。') from None
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password or port not in (None,443 if p.scheme=='https' else 80):raise PageError('公開HTTPページ以外は取得しません。')
    host=p.hostname.encode('idna').decode('ascii')
    if len(url)>3000 or any(ord(c)<32 for c in url) or host.endswith(('.local','.localhost','.internal')):raise PageError('取得対象外のURLです。')
    try:addresses={r[4][0] for r in socket.getaddrinfo(host,443 if p.scheme=='https' else 80,type=socket.SOCK_STREAM)}
    except OSError:raise PageError('サイトの接続先を確認できません。') from None
    if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):raise PageError('ローカル・非公開ネットワークのページは取得しません。')
    return p,host,sorted(addresses)[0]

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.skip=[];self.parts=[];self.title=[];self.in_title=False;self.published=''
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag in ('script','style','noscript','svg','nav','footer','form','template'):
            self.skip.append(tag);return
        if self.skip:return
        if tag=='title':self.in_title=True
        if tag in ('p','div','section','article','li','h1','h2','h3','br'):self.parts.append('\n')
        if tag=='meta' and (attrs.get('property') or attrs.get('name')) in ('article:published_time','datePublished','date'):
            value=attrs.get('content','')
            if re.match(r'^\d{4}-\d{2}-\d{2}(?:T|$)',value):self.published=value[:25]
    def handle_endtag(self,tag):
        if self.skip:
            if tag==self.skip[-1]:self.skip.pop()
            return
        if tag=='title':self.in_title=False
        if tag in ('p','div','section','article','li','h1','h2','h3'):self.parts.append('\n')
    def handle_data(self,value):
        if self.skip:return
        if self.in_title:self.title.append(value)
        else:self.parts.append(value)
    def result(self):
        text='\n'.join(' '.join(line.split()) for line in ''.join(self.parts).splitlines() if line.strip())[:50000]
        title=' '.join(''.join(self.title).split())[:200]
        if len(text)<80:raise PageError('本文を十分に読み取れません。JavaScriptやログインが必要な可能性があります。')
        if re.search(r'^(just a moment|access denied|verify you are human|attention required)',title,re.I):raise PageError('アクセス確認画面のため本文を取得しませんでした。')
        return dict(title=title,text=text,published=self.published)

def fetch_page(url):
    started=time.monotonic()
    for redirect in range(4):
        if time.monotonic()-started>=15:raise PageError('ページ取得が時間切れになりました。')
        p,host,address=target(url)
        timeout=max(.1,15-(time.monotonic()-started))
        connection=(PublicHTTPS if p.scheme=='https' else PublicHTTP)(host,address,timeout)
        try:
            path=urlunsplit(('','',p.path or '/',p.query,''))
            connection.request('GET',path,headers={'User-Agent':'Tomeris/0.26 source-reader','Accept':'text/html,text/plain','Accept-Encoding':'identity','Host':host})
            response=connection.getresponse()
            if response.status in (301,302,303,307,308):
                location=response.getheader('Location')
                if not location:raise PageError('転送先を確認できません。')
                url=urljoin(url,location);continue
            if response.status!=200:raise PageError(f'本文を取得できませんでした（HTTP {response.status}）。')
            mime=response.getheader('Content-Type','').lower()
            if not (mime.startswith('text/html') or mime.startswith('text/plain')):raise PageError('HTML・テキスト以外の形式は未対応です。')
            if response.getheader('Content-Encoding','identity').lower() not in ('','identity'):raise PageError('圧縮された応答形式には未対応です。')
            chunks=[];size=0
            while True:
                remaining=15-(time.monotonic()-started)
                if remaining<=0:raise PageError('本文取得が時間切れになりました。')
                # read1 returns available bytes so the deadline is checked between reads.
                if connection.sock:connection.sock.settimeout(remaining)
                chunk=response.read1(min(16384,1000001-size))
                if not chunk:break
                chunks.append(chunk);size+=len(chunk)
                if size>1000000:raise PageError('ページが大きすぎるため取得を中止しました。')
            raw=b''.join(chunks)
            encoding=re.search(r'charset=["\s]*([\w-]+)',mime)
            try:text=raw.decode(encoding[1] if encoding else 'utf-8',errors='replace')
            except LookupError:text=raw.decode('utf-8',errors='replace')
            if mime.startswith('text/plain'):
                if len(text.strip())<80:raise PageError('本文が短すぎます。')
                result=dict(title=host,text=text[:50000],published='')
            else:
                parser=PageParser();parser.feed(text);result=parser.result()
            result['url']=url
            return result
        except (OSError,http.client.HTTPException,UnicodeError) as exc:raise PageError('本文の通信に失敗しました。') from exc
        finally:connection.close()
    raise PageError('転送回数が多すぎるため停止しました。')
