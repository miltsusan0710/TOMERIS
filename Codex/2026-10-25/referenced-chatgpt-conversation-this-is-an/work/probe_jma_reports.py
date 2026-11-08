from urllib.request import urlopen
from pathlib import Path
import xml.etree.ElementTree as E
root=E.fromstring(Path('work/jma_feed_sample.xml').read_bytes())
for i,e in enumerate(root.findall('{*}entry')[:2]):
 url=e.find('{*}link').get('href')
 with urlopen(url,timeout=15) as r:raw=r.read(1500000)
 Path(f'work/jma_report_{i}.xml').write_bytes(raw)
 print(raw.decode('utf-8')[:6500])
