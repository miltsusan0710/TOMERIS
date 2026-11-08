import sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
base=Path(__file__).resolve().parents[1];sys.path.insert(0,str(base/'outputs'))
from tomeris_desktop_v080 import DesktopService
with tempfile.TemporaryDirectory(dir=base/'work'/'v07') as folder:
 s=DesktopService(Path(folder),demo=True)
 try:
  s.web_chat('荒川区立第一中学校はどこ？','unused',automatic=True)
  s.demo=False
  with patch('tomeris_capabilities.LocalProvider.generate',side_effect=AssertionError('model must not answer principal')):
   _,answer=s.prepare_context('校長は誰？')
  assert '荒川区立第一中学校の校長' in answer
  assert '【校長の紹介】' not in answer
  with (base/'work'/'v080_live_context_result.json').open('x',encoding='utf-8') as f:json.dump(dict(answer=answer),f,ensure_ascii=False,indent=2)
  print(answer)
 finally:s.close()
