import sys,json,time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
sys.path.insert(0,str(Path('outputs').resolve()))
from tomeris_desktop_v038 import DesktopService
from tomeris_search_methods import wikipedia_search,wikipedia_page,MethodError
from tomeris_page_reader import fetch_page,PageError
root=Path('work/v07')
result={'mode':'one_public_source_live_check','query':'Ollama','limits':'検索候補なしの部分だけ模擬。本文取得は実通信。1件の検証で一般化しない。'}
try:
 rows=wikipedia_search('Ollama');row=next(r for r in rows if r['title'].casefold()=='ollama')
 page=wikipedia_page(row);result['api_body_chars']=len(page['text']);result['url']=page['url']
 with TemporaryDirectory(dir=root) as folder:
  s=DesktopService(Path(folder),demo=True);s.demo=False
  try:
   s.catalogue.learn([dict(page=page,excerpts=[page['text'][:800]])])
   start=time.perf_counter()
   with patch('tomeris_search_methods.wikipedia_search',return_value=[]),patch('tomeris_search_methods.search_web',return_value=[]):
    answer=s.web_chat('Ollamaについて調べて','unused',automatic=True)
   result['seconds']=round(time.perf_counter()-start,2);result['shown_sources']=[x['page']['url'] for x in s.last_evidence_items];result['answer']=answer
  finally:s.close()
except (MethodError,PageError,StopIteration) as exc:result['error']=str(exc)
Path('outputs/source_learning_live_check_v038.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
