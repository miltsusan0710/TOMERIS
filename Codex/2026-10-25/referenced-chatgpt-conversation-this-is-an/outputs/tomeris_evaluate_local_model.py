"""Record real local-model responses to fixed questions, without self-grading."""
import hashlib,importlib,json,re,tempfile,time
from pathlib import Path
from datetime import datetime,timezone
from tomeris_evaluate_behavior import MODEL_CASES
from tomeris_provider import ProviderError

def run():
 root=Path(__file__).resolve().parent;module=re.search(r'from (tomeris_desktop_v\d+) import main',(root/'tomeris_desktop.py').read_text(encoding='utf-8-sig'))[1]
 cls=importlib.import_module(module).DesktopService
 stamp=datetime.now(timezone.utc);out=root/'evaluations';out.mkdir(exist_ok=True)
 path=out/('local_model_'+stamp.strftime('%Y%m%dT%H%M%S_%fZ')+'.json')
 result=dict(app_module=module,created_at=stamp.isoformat(),model='qwen2.5:3b',status='running',cases=[],limits='一回のローカルモデル出力の記録。比較対象なし。自己採点なし。能力向上の証明ではない。固定質問だけをlocalhostのOllamaへ送信。本番記憶・計画は使用しない。')
 def save():path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 save()
 try:
  for case in MODEL_CASES:
   with tempfile.TemporaryDirectory(dir=root.parent/'work'/'v07') as folder:
    s=cls(Path(folder),demo=True);s.demo=False
    try:
     names=s.models()
     if result['model'] not in names:raise ProviderError('指定モデルが導入されていません。')
     started=time.perf_counter();print(case['id']+' generating...',flush=True)
     answer=s.chat(case['question'],result['model'])
     result['cases'].append(dict(**case,answer=answer,seconds=round(time.perf_counter()-started,2),assessment='pending_human_review'))
     save();print(case['id']+' recorded',flush=True)
    finally:s.close()
  result['status']='recorded'
 except (ProviderError,OSError,ValueError) as exc:
  result['status']='incomplete';result['error']=str(exc)
 finally:save()
 print(str(path),flush=True);return result
if __name__=='__main__':run()
