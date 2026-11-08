from urllib.request import Request,urlopen
from urllib.parse import urlencode
import json
for lang,q in [('ja','アイアンマン'),('en','Iron Man')]:
    url=f'https://{lang}.wikipedia.org/w/rest.php/v1/search/page?'+urlencode({'q':q,'limit':3})
    try:
        data=json.load(urlopen(Request(url,headers={'User-Agent':'Tomeris/0.27 (local desktop research tool)'}),timeout=12))
        print(lang,[(r.get('title'),r.get('key')) for r in data.get('pages',[])])
    except Exception as e: print(lang,type(e).__name__,str(e))
