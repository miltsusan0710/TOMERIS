import sys,json,tempfile
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,'outputs')
from tomeris_desktop_v064 import DesktopService
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
 s=DesktopService(Path(folder),demo=True);s.demo=False
 try:
  q='トニースタークについて調べて'
  answer=s.web_chat(q,'unused',automatic=True);print(answer,flush=True)
  path=Path('outputs/evaluations')/('tony_live_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json')
  path.write_text(json.dumps(dict(question=q,answer=answer),ensure_ascii=False,indent=2),encoding='utf-8');print(path)
 finally:s.close()
