"""Read-only multi-account Google Calendar for the Windows desktop app."""
import base64
import ctypes
from ctypes import wintypes
from datetime import datetime, time as day_time, timedelta, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import secrets
import tempfile
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, parse_qs, quote
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
import webbrowser

JST=timezone(timedelta(hours=9))
AUTH='https://accounts.google.com/o/oauth2/v2/auth'
TOKEN='https://oauth2.googleapis.com/token'
USERINFO='https://openidconnect.googleapis.com/v1/userinfo'
CALENDAR='https://www.googleapis.com/calendar/v3/'
SCOPES=('openid','email','https://www.googleapis.com/auth/calendar.calendarlist.readonly',
        'https://www.googleapis.com/auth/calendar.events.readonly')

class GoogleError(RuntimeError):
    def __init__(self,message,status=None):
        super().__init__(message)
        self.status=status

def protect(raw,decrypt=False):
    """DPAPI current-user encryption. No plaintext fallback."""
    if os.name!='nt':
        raise GoogleError('Google接続情報の保存はWindowsで利用してください。')
    class Blob(ctypes.Structure):
        _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]
    crypt=ctypes.WinDLL('crypt32',use_last_error=True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.LocalFree.argtypes=[ctypes.c_void_p]; kernel.LocalFree.restype=ctypes.c_void_p
    buffer=ctypes.create_string_buffer(raw)
    src=Blob(len(raw),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_ubyte))); dst=Blob()
    function=crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,
                       ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    function.restype=wintypes.BOOL
    if not function(ctypes.byref(src),None,None,None,None,1,ctypes.byref(dst)):
        raise GoogleError('Windowsによる接続情報の保護／読込に失敗しました。元のWindowsユーザーで開いてください。')
    try:
        return ctypes.string_at(dst.data,dst.size)
    finally:
        kernel.LocalFree(ctypes.cast(dst.data,ctypes.c_void_p))

class Vault:
    def __init__(self,directory):
        self.path=Path(directory)/'google_connection.dpapi'
    def read(self):
        if not self.path.exists():
            return {'version':1,'client':None,'accounts':{}}
        try:
            if self.path.stat().st_size>2*1024*1024:
                raise ValueError()
            data=json.loads(protect(self.path.read_bytes(),decrypt=True))
            if data.get('version')!=1 or not isinstance(data.get('accounts'),dict):
                raise ValueError()
            return data
        except (ValueError,TypeError,AttributeError):
            raise GoogleError('Google接続情報の形式が不正です。既存のファイルは変更しません。') from None
    def write(self,data):
        encrypted=protect(json.dumps(data,ensure_ascii=False).encode('utf-8'))
        fd,name=tempfile.mkstemp(prefix='google_',suffix='.tmp',dir=self.path.parent)
        try:
            with os.fdopen(fd,'wb') as handle:
                handle.write(encrypted); handle.flush(); os.fsync(handle.fileno())
            os.replace(name,self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

def request_json(url,form=None,token=None):
    if not (url==TOKEN or url==USERINFO or url.startswith(CALENDAR)):
        raise GoogleError('許可されていない接続先です。')
    if form is not None and url!=TOKEN:
        raise GoogleError('カレンダーへの書き込みは実装していません。')
    headers={'Accept':'application/json'}; body=None
    if form is not None:
        headers['Content-Type']='application/x-www-form-urlencoded'
        body=urlencode(form).encode('ascii')
    if token:
        headers['Authorization']='Bearer '+token
    try:
        with build_opener(ProxyHandler({}),NoRedirect()).open(Request(url,data=body,headers=headers),timeout=20) as response:
            raw=response.read(4*1024*1024+1)
        if len(raw)>4*1024*1024:
            raise ValueError()
        result=json.loads(raw)
        if not isinstance(result,dict):
            raise ValueError()
        return result
    except HTTPError as exc:
        status=exc.code; exc.close()
        text={400:'認証が期限切れ、または設定が一致しません。再接続してください。',
              401:'認証が無効です。アカウントを再接続してください。',
              403:'Calendar APIの有効化、閲覧権限、組織の制限を確認してください。',
              429:'Googleの利用上限です。時間をおいて再試行してください。'}.get(status,'Googleへの接続に失敗しました。')
        raise GoogleError(f'{text}（HTTP {status}）',status) from None
    except (URLError,OSError,ValueError):
        raise GoogleError('Googleと通信できないか、応答を読み取れませんでした。') from None

def auth_parameters(client_id,redirect,state,verifier):
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode('ascii')).digest()).rstrip(b'=').decode('ascii')
    return {'client_id':client_id,'redirect_uri':redirect,'response_type':'code','scope':' '.join(SCOPES),
            'access_type':'offline','prompt':'consent select_account','state':state,
            'code_challenge':challenge,'code_challenge_method':'S256'}

def parse_callback(path,state):
    parts=urlsplit(path)
    if parts.path!='/oauth2callback':
        return None
    values=parse_qs(parts.query); received=values.get('state',[])
    if len(received)!=1 or not secrets.compare_digest(received[0].encode('utf-8'),state.encode('utf-8')):
        return None
    if 'error' in values:
        raise GoogleError('Googleの接続許可がキャンセルされました。')
    codes=values.get('code',[])
    return codes[0] if len(codes)==1 and 0<len(codes[0])<=4096 else None

def authorize(client,cancel,timeout=180):
    if cancel.is_set():
        raise GoogleError('Google接続を中止しました。')
    state,verifier=secrets.token_urlsafe(32),secrets.token_urlsafe(64)
    result={}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass
        def do_GET(self):
            try:
                code=parse_callback(self.path,state)
                if code:
                    result['code']=code
            except GoogleError as exc:
                result['error']=exc
            valid=bool(result)
            body=('Googleの応答を受け取りました。このタブを閉じてトメリスに戻ってください。' if valid else 'このリクエストは受け付けられません。').encode('utf-8')
            self.send_response(200 if valid else 400)
            self.send_header('Content-Type','text/plain; charset=utf-8')
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('Referrer-Policy','no-referrer')
            self.end_headers()
            try:
                self.wfile.write(body)
            except OSError:
                pass
    class Server(HTTPServer):
        def get_request(self):
            sock,addr=super().get_request(); sock.settimeout(1)
            return sock,addr
        def handle_error(self,request,client_address):
            pass
    with Server(('127.0.0.1',0),Handler) as server:
        server.timeout=0.3
        redirect=f'http://127.0.0.1:{server.server_port}/oauth2callback'
        if not webbrowser.open(AUTH+'?'+urlencode(auth_parameters(client['client_id'],redirect,state,verifier))):
            raise GoogleError('ブラウザーを開けませんでした。既定のブラウザーを設定してください。')
        deadline=time.monotonic()+timeout
        while not result and not cancel.is_set() and time.monotonic()<deadline:
            server.handle_request()
    if cancel.is_set():
        raise GoogleError('Google接続を中止しました。')
    if 'error' in result:
        raise result['error']
    if not result:
        raise GoogleError('接続待ちが時間切れになりました。もう一度「アカウントを追加」を押してください。')
    return request_json(TOKEN,form={**client,'code':result['code'],'code_verifier':verifier,
                                   'redirect_uri':redirect,'grant_type':'authorization_code'})

def normalize_token(result,previous=None):
    previous=previous or {}
    granted=set(result.get('scope',' '.join(SCOPES)).split())
    allowed=set(SCOPES)|{'https://www.googleapis.com/auth/userinfo.email'}
    if not set(SCOPES[2:]).issubset(granted) or not granted.issubset(allowed):
        raise GoogleError('読み取り権限が不足、または余分な権限があります。専用のOAuthクライアントを使用してください。')
    access=result.get('access_token'); refresh=result.get('refresh_token') or previous.get('refresh_token')
    if not isinstance(access,str) or not access or not isinstance(refresh,str) or not refresh:
        raise GoogleError('接続情報が不足しています。アカウントを再接続してください。')
    try:
        expiry=int(result['expires_in'])
        if expiry<=0:
            raise ValueError()
    except (KeyError,ValueError,TypeError):
        raise GoogleError('認証の有効期限を読み取れませんでした。') from None
    return {'access_token':access,'refresh_token':refresh,'expires_at':time.time()+expiry}

class GoogleCalendar:
    def __init__(self,directory):
        self.vault=Vault(directory); self.cancel=threading.Event()
    def status(self):
        data=self.vault.read()
        return {'configured':bool(data['client']),'accounts':[{'id':key,'email':value['email']} for key,value in data['accounts'].items()]}
    def configure(self,path):
        try:
            with open(path,'rb') as handle:
                raw=handle.read(65537)
            if len(raw)>65536:
                raise ValueError()
            client=json.loads(raw)['installed']; cid,secret=client['client_id'],client['client_secret']
            if not isinstance(cid,str) or not cid.endswith('.apps.googleusercontent.com') or not isinstance(secret,str) or not secret:
                raise ValueError()
        except (OSError,ValueError,KeyError,TypeError):
            raise GoogleError('Googleで作成した「デスクトップアプリ」の認証JSONを選んでください。') from None
        data=self.vault.read(); new={'client_id':cid,'client_secret':secret}
        if data['accounts'] and data['client']!=new:
            raise GoogleError('別の設定に変える場合は、先に登録アカウントをすべてこのアプリから削除してください。')
        data['client']=new; self.vault.write(data)
        return self.status()
    def connect(self):
        data=self.vault.read()
        if not data['client']:
            raise GoogleError('先に「設定JSONを選ぶ」でGoogleの認証設定を登録してください。')
        token=normalize_token(authorize(data['client'],self.cancel))
        if self.cancel.is_set():
            raise GoogleError('Google接続を中止しました。')
        info=request_json(USERINFO,token=token['access_token'])
        if not isinstance(info.get('sub'),str) or not info['sub'] or not isinstance(info.get('email'),str) or info.get('email_verified') is not True:
            raise GoogleError('Googleアカウントの識別情報を確認できませんでした。')
        if self.cancel.is_set():
            raise GoogleError('Google接続を中止しました。')
        data['accounts'][info['sub']]={'email':info['email'],**token}
        self.vault.write(data)
        return self.status()
    def forget(self,account_id):
        data=self.vault.read()
        if account_id not in data['accounts']:
            raise GoogleError('削除するアカウントを選んでください。')
        del data['accounts'][account_id]; self.vault.write(data)
        return self.status()
    def _get(self,data,account_id,path,params):
        account=data['accounts'][account_id]
        def refresh():
            updated=normalize_token(request_json(TOKEN,form={**data['client'],'grant_type':'refresh_token','refresh_token':account['refresh_token']}),account)
            account.update(updated); self.vault.write(data)
        if account.get('expires_at',0)<=time.time()+60:
            refresh()
        if self.cancel.is_set():
            raise GoogleError('予定の取得を中止しました。')
        url=CALENDAR+path+'?'+urlencode(params)
        try:
            return request_json(url,token=account['access_token'])
        except GoogleError as exc:
            if exc.status!=401:
                raise
            refresh()
            if self.cancel.is_set():
                raise GoogleError('予定の取得を中止しました。')
            return request_json(url,token=account['access_token'])
    def _pages(self,data,account_id,path,params):
        items,seen=[],set()
        for _ in range(20):
            if self.cancel.is_set():
                raise GoogleError('予定の取得を中止しました。')
            page=self._get(data,account_id,path,params); batch=page.get('items',[])
            if not isinstance(batch,list):
                raise GoogleError('カレンダーの応答形式が不正です。')
            items.extend(batch); next_page=page.get('nextPageToken')
            if not next_page:
                return items
            if not isinstance(next_page,str) or next_page in seen:
                raise GoogleError('カレンダーのページ情報が不正です。')
            seen.add(next_page); params={**params,'pageToken':next_page}
        raise GoogleError('予定が多すぎるため取得を中断しました。Googleカレンダーで確認してください。')
    def agenda(self,account_id=None,now=None):
        data=self.vault.read(); keys=[account_id] if account_id else list(data['accounts'])
        if not keys:
            return 'Googleアカウントが未登録です。「アカウントを追加」から接続してください。'
        if any(key not in data['accounts'] for key in keys):
            raise GoogleError('アカウントを選び直してください。')
        now=(now or datetime.now(JST)).astimezone(JST)
        start=datetime.combine(now.date(),day_time(),JST); end=start+timedelta(days=1)
        lines=[f'Googleカレンダー / {start.date()}（日本時間）','閲覧のみ・Googleで表示対象のカレンダー。取得時点の予定です。']
        for key in keys:
            lines.append('\n【'+data['accounts'][key]['email']+'】')
            try:
                calendars=self._pages(data,key,'users/me/calendarList',{'maxResults':250,'minAccessRole':'reader'})
                calendars=[c for c in calendars if not c.get('hidden') and not c.get('deleted') and c.get('selected',True)]
                if len(calendars)>100:
                    raise GoogleError('カレンダーが100件を超えるため取得できません。表示対象を減らしてください。')
                rows,errors=[],[]
                for calendar in calendars:
                    if self.cancel.is_set():
                        raise GoogleError('予定の取得を中止しました。')
                    name=calendar.get('summaryOverride') or calendar.get('summary') or 'カレンダー'
                    try:
                        events=self._pages(data,key,'calendars/'+quote(calendar['id'],safe='')+'/events',
                            {'timeMin':start.isoformat(),'timeMax':end.isoformat(),'timeZone':'Asia/Tokyo',
                             'singleEvents':'true','orderBy':'startTime','showDeleted':'false','maxResults':250,
                             'fields':'nextPageToken,items(id,status,summary,start,end)'})
                        for event in events:
                            if event.get('status')=='cancelled':
                                continue
                            begin,finish=event['start'],event['end']
                            if 'date' in begin:
                                stamp,label=start,'終日'
                            else:
                                stamp=datetime.fromisoformat(begin['dateTime'].replace('Z','+00:00'))
                                stop=datetime.fromisoformat(finish['dateTime'].replace('Z','+00:00'))
                                if stamp.tzinfo is None or stop.tzinfo is None:
                                    raise ValueError()
                                stamp,stop=stamp.astimezone(JST),stop.astimezone(JST)
                                fmt=lambda t:t.strftime('%H:%M' if t.date()==start.date() else '%m/%d %H:%M')
                                label=fmt(stamp)+'〜'+fmt(stop)
                            rows.append((stamp,f"{label}  {event.get('summary') or '（非公開・件名なし）'}  ［{name}］"))
                    except (GoogleError,KeyError,ValueError,TypeError):
                        errors.append(f'取得できないカレンダー：{name}。権限や接続を確認してください。')
                lines.extend(text for _,text in sorted(rows,key=lambda row:row[0]))
                if not rows and not errors:
                    lines.append('今日の予定はありません。')
                lines.extend(errors)
            except GoogleError as exc:
                lines.append('取得できませんでした：'+str(exc))
        return '\n'.join(lines)
