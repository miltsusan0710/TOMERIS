import sys,json,tempfile,time
from pathlib import Path
from datetime import datetime,timezone
base=Path(__file__).resolve().parents[1];sys.path.insert(0,str(base/'outputs'))
from tomeris_desktop_v084 import DesktopService
cases=[['少し疲れた。今日の作業を始めるための工夫を2つだけ教えて。','2番をもっと短く説明して。'],
       ['新しい手順にしたらミスが減った。この手順のおかげと断定できる？'],
       ['少し休憩して雑談しよう。'],['計算: 1250*3+980'],['今日の予定は？'],['明後日の天気は？']]
rows=[]
for turns in cases:
 with tempfile.TemporaryDirectory(dir=base/'work'/'v07') as folder:
  s=DesktopService(Path(folder),source=Path(folder)/'no_import.json',demo=False)
  try:
   s.models()
   for q in turns:
    start=time.monotonic();answer=s.web_chat(q,'qwen2.5:3b',automatic=True)
    rows.append(dict(question=q,answer=answer,seconds=round(time.monotonic()-start,2)))
    print(q,answer[:180],flush=True)
  finally:s.close()
(base/'work'/'v084_conversation_audit.json').write_text(json.dumps(dict(checked_at=datetime.now(timezone.utc).isoformat(),rows=rows),ensure_ascii=False,indent=2),encoding='utf-8')
