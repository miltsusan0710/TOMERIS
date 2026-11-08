from urllib.request import Request,urlopen
from urllib.parse import urlencode
import json
for lang,q in [('ja','アイアンマン'),('ja','Ollama'),('en','Ollama')]:
    url=f'https://{lang}.wikipedia.org/w/api.php?'+urlencode(dict(action='query',list='search',srsearch=q,srlimit=3,format='json',utf8=1))
    try:
        d=json.load(urlopen(Request(url,headers={'User-Agent':'Tomeris/0.27 (local desktop research tool)'}),timeout=12))
        print(lang,q,[(r['title'],r['pageid']) for r in d.get('query',{}).get('search',[])])
    except Exception as e:print(type(e).__name__,str(e))
