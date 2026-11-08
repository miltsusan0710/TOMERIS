import sys
from pathlib import Path
sys.path.insert(0,str(Path('outputs').resolve()))
import tomeris_grounded_summary as summary
from tomeris_page_reader import fetch_page
from tomeris_evidence_report import passages
p=fetch_page('https://ollama.com/');pages=[dict(page=p,excerpts=passages(p,'Ollama'))]
base=summary.LocalProvider
class Captured(base):
    def generate(self,messages):
        result=super().generate(messages)
        Path('work/evidence_summary_raw.txt').write_text(result,encoding='utf-8')
        return result
summary.LocalProvider=Captured
result=summary.summarize('Ollamaでは何ができる？',pages,'qwen2.5:3b')
print('Summary accepted:',bool(result),flush=True)
if result:print(result,flush=True)
