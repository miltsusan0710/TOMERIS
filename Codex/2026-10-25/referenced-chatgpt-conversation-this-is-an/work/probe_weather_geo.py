from urllib.request import urlopen
from urllib.parse import urlencode
import json
for name in ['平塚市','平塚','荒川区']:
    try:
        u='https://geocoding-api.open-meteo.com/v1/search?'+urlencode(dict(name=name,count=5,language='ja',countryCode='JP'))
        data=json.load(urlopen(u,timeout=12))
        print(name,[(x['name'],x.get('admin1'),x.get('admin2'),x['latitude'],x['longitude']) for x in data.get('results',[])])
    except Exception as e: print(type(e).__name__,str(e))
