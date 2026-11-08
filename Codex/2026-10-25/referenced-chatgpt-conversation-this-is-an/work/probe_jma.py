from urllib.request import urlopen
from pathlib import Path
import xml.etree.ElementTree as E
url='https://www.data.jma.go.jp/developer/xml/feed/eqvol.xml'
with urlopen(url,timeout=15) as r:raw=r.read(1500000)
Path('work/jma_feed_sample.xml').write_bytes(raw)
root=E.fromstring(raw)
print('feed updated',root.findtext('{*}updated'))
for e in root.findall('{*}entry')[:8]:print(e.findtext('{*}title'),e.findtext('{*}updated'),e.find('{*}link').get('href'))
