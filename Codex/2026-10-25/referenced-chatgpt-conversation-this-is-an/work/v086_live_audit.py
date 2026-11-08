"""Isolated real retrieval audit; no production memory or learned policy writes."""
import sys,json,tempfile,time
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
base=Path(__file__).resolve().parents[1];sys.path.insert(0,str(base/'outputs'))
from tomeris_desktop_v086 import DesktopService
cases=[('regression','東海大学について知りたい'),('regression','東京大学について知りたい'),
       ('holdout','光合成について教えて'),('holdout','マリー・キュリーについて説明して'),
       ('holdout','徳川家康とは何ですか？'),('holdout','Ollamaについて知りたい'),
       ('holdout','水の循環について知りたい'),('holdout','国立科学博物館について知りたい')]
cases=cases[:3]
results=[]
if '--holdout' in sys.argv:
 cases=[('holdout2',q) for q in ('富士山とは何ですか？','周期表について知りたい','フィンセント・ファン・ゴッホについて教えて','蒸気機関について説明して')]
with tempfile.TemporaryDirectory(dir=base/'work'/'v07') as folder:
 s=DesktopService(Path(folder),source=Path(folder)/'no_import.json',demo=False)
 try:
  for split,q in cases:
   started=time.monotonic()
   # A factual query must not call the conversation generator, even on network failure.
   with patch('tomeris_capabilities.LocalProvider.generate',side_effect=AssertionError('ungrounded model fallback')):
    answer=s.web_chat(q,'qwen2.5:3b',automatic=True)
   items=getattr(s,'last_evidence_items',[])
   rows=[dict(title=x['page']['title'],url=x['page']['url'],excerpts=x['excerpts'],
              verbatim=all(t in x['page']['text'] for t in x['excerpts'])) for x in items]
   results.append(dict(split=split,question=q,seconds=round(time.monotonic()-started,2),answer=answer,evidence=rows))
   print(q, 'evidence_pages=',len(rows),flush=True)
 finally:s.close()
out=base/'work'/('v086_holdout.json' if '--holdout' in sys.argv else 'v086_live_audit.json')
out.write_text(json.dumps(dict(checked_at=datetime.now(timezone.utc).isoformat(),results=results),ensure_ascii=False,indent=2),encoding='utf-8')
print(out)

