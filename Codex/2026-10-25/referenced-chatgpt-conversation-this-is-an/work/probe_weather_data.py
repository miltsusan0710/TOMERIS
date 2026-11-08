from urllib.request import urlopen
from urllib.parse import urlencode
import json
for name in ['Arakawa-ku','Arakawa','東京都荒川区']:
    u='https://geocoding-api.open-meteo.com/v1/search?'+urlencode(dict(name=name,count=10,language='ja',countryCode='JP'))
    data=json.load(urlopen(u,timeout=12))
    print(name,[(x['name'],x.get('admin1'),x.get('admin2'),x['latitude'],x['longitude']) for x in data.get('results',[])])
u='https://api.open-meteo.com/v1/forecast?'+urlencode(dict(latitude=35.32785,longitude=139.33736,daily='weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max',timezone='Asia/Tokyo',forecast_days=2))
data=json.load(urlopen(u,timeout=15));print('FORECAST',data.get('daily'),data.get('daily_units'))
