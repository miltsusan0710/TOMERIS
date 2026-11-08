import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
from tomeris_evidence_report import DesktopService
with tempfile.TemporaryDirectory(dir='work/v07') as folder:
    s=DesktopService(folder,demo=True);s.demo=False
    try:
        models=s.models();model='qwen2.5:3b' if 'qwen2.5:3b' in models else 'missing'
        print('Model:',model,flush=True)
        answer=s.web_chat('https://ollama.com/ 何ができるか調べて',model,automatic=True,progress=lambda msg:print(msg,flush=True))
        Path('work/evidence_direct_live.txt').write_text(answer,encoding='utf-8')
        print('Finished; grounded summary:', '【資料に基づく整理' in answer,'body evidence:', '【本文で確認した' in answer,flush=True)
    finally:s.close()
