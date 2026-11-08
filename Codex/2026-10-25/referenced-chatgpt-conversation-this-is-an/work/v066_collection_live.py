import sys,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
from tomeris_collection_rotation import DesktopService
tempfile.tempdir=str(Path('work/v07').resolve())
with tempfile.TemporaryDirectory() as d:
 s=DesktopService(Path(d),demo=True)
 try:
  s.demo=False
  for _ in range(2):
   s.auto_sources_next=0
   print(s.collect_public_topic())
  Path('work/v066_collection_live.json').write_text(json.dumps(s.topic_results,ensure_ascii=False,indent=2),encoding='utf-8')
 finally:s.close()
