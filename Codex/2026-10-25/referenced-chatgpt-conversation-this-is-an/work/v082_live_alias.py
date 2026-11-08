import sys,tempfile,json
from pathlib import Path
base=Path(__file__).resolve().parents[1];sys.path.insert(0,str(base/'outputs'))
from tomeris_school_alias import DesktopService
with tempfile.TemporaryDirectory(dir=base/'work'/'v07') as folder:
 s=DesktopService(Path(folder),demo=True);s.demo=False
 try:
  answer=s.web_chat('本所高校について調べて','unused',automatic=True)
  with (base/'work'/'v082_live_alias_result.json').open('x',encoding='utf-8') as f:json.dump(dict(answer=answer),f,ensure_ascii=False,indent=2)
  print(answer)
  assert s.last_evidence_items, 'No excerpt retrieved'
  assert all(item['page']['title']=='東京都立本所高等学校' for item in s.last_evidence_items)
 finally:s.close()
