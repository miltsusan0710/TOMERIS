import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
from tomeris_multisearch_service import DesktopService
from tomeris_search_methods import wikipedia_search,wikipedia_page
for term in ['アイアンマン','Ollama']:
    rows=wikipedia_search(term)
    print(term,'search count:',len(rows),flush=True)
    if rows:
        p=wikipedia_page(rows[0]);print('Article:',p['title'],'body chars:',len(p['text']),'updated:',p['updated'],flush=True)
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    s=DesktopService(folder,demo=True);s.demo=False
    try:
        answer=s.web_chat('アイアンマンについて調べて','missing',automatic=True,progress=lambda x:print(x,flush=True))
        Path('work/multisearch_live_report.txt').write_text(answer,encoding='utf-8')
        print('Body report:', '【対象語が含まれる本文' in answer, 'generated summary:', 'AI作成' in answer,flush=True)
    finally:s.close()
