import sys, json, tempfile, time, importlib
from pathlib import Path
from datetime import datetime, timezone
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'outputs'))
from tomeris_evaluate_behavior import MODEL_CASES
cases = MODEL_CASES + [dict(id='held_out_attendance', question='朝会を短くしたら遅刻が減った。短縮の効果があったと断定できる？', criteria=['報告と検証済み事実を区別', '人数や比較期間を確認', '他の条件も含めた検証方法'])]
path = root / 'outputs' / 'evaluations' / ('analysis_comparison_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ') + '.json')
result = dict(status='running', cases=[], limits='各条件1回、同じローカルモデル、毎回新しい一時データ。自己採点なし。速度比較や能力向上の証明ではない。')
def save():
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
save()
try:
    for module in ('tomeris_desktop_v051', 'tomeris_desktop_v052'):
        cls = importlib.import_module(module).DesktopService
        for case in cases:
            with tempfile.TemporaryDirectory(dir=root / 'work' / 'v07') as folder:
                service = cls(Path(folder), demo=True)
                try:
                    service.demo = False
                    if 'qwen2.5:3b' not in service.models():
                        raise RuntimeError('model missing')
                    print(module + ' ' + case['id'], flush=True)
                    start = time.perf_counter()
                    answer = service.chat(case['question'], 'qwen2.5:3b')
                    result['cases'].append(dict(**case, module=module, answer=answer, seconds=round(time.perf_counter()-start, 2), assessment='pending_human_review'))
                    save()
                finally:
                    service.close()
    result['status'] = 'recorded'
except Exception as exc:
    result['status'] = 'incomplete'
    result['error'] = str(exc)
finally:
    save()
    print(path, flush=True)
