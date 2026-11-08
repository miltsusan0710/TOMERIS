"""Read-only Open-Meteo forecast with explicit place matching and JST date checks."""
from datetime import datetime, timezone, timedelta
import json
import math
import re
from urllib.parse import urlencode
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import URLError

JST=timezone(timedelta(hours=9))
class WeatherError(ValueError): pass
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): raise WeatherError('天気サービスから転送を求められたため停止しました。')

def read_json(url):
    try:
        with build_opener(NoRedirect()).open(Request(url,headers={'User-Agent':'Tomeris/0.24.1 weather'}),timeout=12) as response:
            if response.status!=200: raise WeatherError('天気サービスが利用できません。')
            raw=response.read(500001)
        if len(raw)>500000: raise WeatherError('天気データが大きすぎます。')
        data=json.loads(raw)
        if not isinstance(data,dict) or data.get('error'): raise WeatherError('天気サービスの応答を確認できませんでした。')
        return data
    except (URLError,OSError,TimeoutError,ValueError) as exc:
        if isinstance(exc,WeatherError): raise
        raise WeatherError('天気データを取得できませんでした。通信状態を確認し、もう一度地域名を送ってください。') from exc

def locate(region):
    prefecture=''; place=region
    match=re.fullmatch(r'(北海道|東京都|大阪府|京都府|.{2,3}県)(.+)',region)
    if match: prefecture,place=match.groups()
    terms=[place]
    if len(place)>2 and place.endswith(('市','区','町','村')): terms.append(place[:-1])
    for term in terms:
        url='https://geocoding-api.open-meteo.com/v1/search?'+urlencode(dict(name=term,count=20,language='ja',countryCode='JP'))
        data=read_json(url); candidates=data.get('results',[])
        if not isinstance(candidates,list): raise WeatherError('地域情報の形式を確認できませんでした。')
        matched=[]
        for row in candidates:
            if not isinstance(row,dict) or row.get('country_code')!='JP': continue
            if prefecture and row.get('admin1')!=prefecture: continue
            if row.get('name')!=place and row.get('admin2')!=place: continue
            lat,lon=row.get('latitude'),row.get('longitude')
            if type(lat) not in (int,float) or type(lon) not in (int,float) or not math.isfinite(lat) or not math.isfinite(lon) or not (-90<=lat<=90 and -180<=lon<=180): continue
            matched.append(row)
        if matched:
            groups={(r.get('admin1'),r.get('admin2') or r.get('name')) for r in matched}
            if len(groups)>1: raise WeatherError('同じ名前の地域が複数あります。都道府県を付けて入力してください。')
            exact=[r for r in matched if r.get('name')==place]
            return (exact or matched)[0]
    raise WeatherError('地域を一意に確認できませんでした。都道府県と市区町村名を入力してください。')

CODES={0:'晴れ',1:'主に晴れ',2:'一部くもり',3:'くもり',45:'霧',48:'着氷性の霧',51:'弱い霧雨',53:'霧雨',55:'強い霧雨',56:'弱い着氷性の霧雨',57:'強い着氷性の霧雨',61:'弱い雨',63:'雨',65:'強い雨',66:'弱い着氷性の雨',67:'強い着氷性の雨',71:'弱い雪',73:'雪',75:'強い雪',77:'霧雪',80:'弱いにわか雨',81:'にわか雨',82:'激しいにわか雨',85:'弱いにわか雪',86:'強いにわか雪',95:'雷雨',96:'ひょうを伴う雷雨',99:'強いひょうを伴う雷雨'}

def fetch_weather(region,day='今日',now=None):
    now=now or datetime.now(JST)
    date=(now.astimezone(JST).date()+timedelta(days=1 if day=='明日' else 0)).isoformat()
    place=locate(region)
    url='https://api.open-meteo.com/v1/forecast?'+urlencode(dict(latitude=place['latitude'],longitude=place['longitude'],daily='weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max',timezone='Asia/Tokyo',forecast_days=2,temperature_unit='celsius'))
    data=read_json(url); daily=data.get('daily',{}); units=data.get('daily_units',{})
    if not isinstance(daily,dict) or not isinstance(units,dict) or data.get('timezone')!='Asia/Tokyo': raise WeatherError('予報の時刻・形式を確認できませんでした。')
    dates=daily.get('time',[])
    if not isinstance(dates,list) or dates.count(date)!=1: raise WeatherError('指定日の予報が返りませんでした。古い予報を今日の天気として表示しません。')
    i=dates.index(date)
    def value(key,unit):
        if units.get(key)!=unit: raise WeatherError('予報の単位を確認できませんでした。')
        values=daily.get(key,[])
        if not isinstance(values,list) or i>=len(values): return None
        v=values[i]
        if v is None: return None
        if type(v) not in (int,float) or not math.isfinite(v): raise WeatherError('予報の数値を確認できませんでした。')
        return v
    code=value('weather_code','wmo code'); high=value('temperature_2m_max','°C'); low=value('temperature_2m_min','°C'); rain=value('precipitation_probability_max','%')
    if all(x is None for x in (code,high,low,rain)): raise WeatherError('指定日の予報が欠測です。')
    if rain is not None and not 0<=rain<=100: raise WeatherError('降水確率の値を確認できませんでした。')
    def fmt(v,suffix): return '未取得' if v is None else f'{v:g}{suffix}'
    area=' '.join(dict.fromkeys(str(place.get(k,'')) for k in ('admin1','admin2','name') if place.get(k)))
    return f'{region}の{day}の予報（{date}・日本時間）\n取得地点：{area}\n天気：{CODES.get(code,"未取得・不明な天気コード")}\n最高気温：{fmt(high,"℃")} ／ 最低気温：{fmt(low,"℃")}\n降水確率（日内最大）：{fmt(rain,"％")}\n\n予報モデルの値です。現地の観測値ではなく、地域全域の天気を保証するものではありません。\n取得：{now.astimezone(JST).strftime("%Y-%m-%d %H:%M JST")}\n出典：Open-Meteo（地点情報：GeoNames）\nhttps://open-meteo.com/\nデータ：{url}'
