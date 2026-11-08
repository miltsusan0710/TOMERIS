import sys,json,tempfile
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,'outputs')
from tomeris_desktop_v061 import DesktopService
results=[]
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
 s=DesktopService(Path(folder),demo=True);s.demo=False
 try:
  for q in ('kunってだれ？','ユーチューバー','桝太一て誰？'):
   answer=s.web_chat(q,'unused',automatic=True);results.append(dict(question=q,answer=answer));print(answer,flush=True)
 finally:s.close()
p=Path('outputs/evaluations')/('people_live_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json')
p.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');print(p)
