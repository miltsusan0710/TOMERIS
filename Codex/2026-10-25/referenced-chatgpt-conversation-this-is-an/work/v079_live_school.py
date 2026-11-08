import sys,tempfile,json
from pathlib import Path
base=Path(__file__).resolve().parents[1];sys.path.insert(0,str(base/'outputs'))
from tomeris_school_location import DesktopService
with tempfile.TemporaryDirectory(dir=base/'work'/'v07') as folder:
 s=DesktopService(Path(folder),demo=True);s.demo=False
 try:
  answers={q:s.web_chat(q,'unused',automatic=True) for q in ('荒川区立第一中学校はどこ？','本所高校はどこ？')}
  with (base/'work'/'v079_live_school_result_fixed.json').open('x',encoding='utf-8') as f:json.dump(answers,f,ensure_ascii=False,indent=2)
  assert '荒川1-30-1' in answers['荒川区立第一中学校はどこ？']
  assert '向島3-37-25' in answers['本所高校はどこ？']
  print(json.dumps(answers,ensure_ascii=False))
 finally:s.close()
