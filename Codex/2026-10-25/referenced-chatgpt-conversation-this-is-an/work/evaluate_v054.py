import sys, json, tempfile, time
from pathlib import Path
from datetime import datetime, timezone
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'outputs'))
from tomeris_desktop_v054 import DesktopService
questions=['工程を変更したら不良が減った。効果があったと断定できる？',
           '前は100個中10個、後は40個中8個。期間はどちらも1週間。',
           '別の話', '今日の予定は？']
out=root/'outputs'/'evaluations'/('ratio_followup_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')+'.json')
result=dict(module='tomeris_desktop_v054',model='qwen2.5:3b',status='running',turns=[],limits='一時データ、前回誤答した複数ターン問題1件の回帰検証。数値比較はAIを呼ばず計算。人による独立評価なし。能力向上の証明ではない。')
try:
 with tempfile.TemporaryDirectory(dir=root/'work'/'v07') as folder:
  s=DesktopService(Path(folder),demo=True)
  try:
   s.demo=False
   assert result['model'] in s.models()
   for q in questions:
    start=time.perf_counter();answer=s.chat(q,result['model'])
    result['turns'].append(dict(question=q,answer=answer,seconds=round(time.perf_counter()-start,2)))
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
  finally:s.close()
 result['status']='recorded'
except Exception as exc:result.update(status='incomplete',error=str(exc))
finally:
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(out)
