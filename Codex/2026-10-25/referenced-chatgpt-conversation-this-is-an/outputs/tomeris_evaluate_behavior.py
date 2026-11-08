"""Repeatable offline behavior evaluation; not an intelligence score."""
import hashlib,importlib,json,re,socket,tempfile,time
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch

CASES=[
 dict(id='calc_decimal',category='数値計算',turns=['計算: 0.1+0.2'],required=['結果：0.3'],forbidden=[]),
 dict(id='calc_precedence',category='数値計算',turns=['計算: 2+3*4'],required=['結果：14'],forbidden=[]),
 dict(id='calc_zero',category='数値計算',turns=['計算: 1/0'],required=['0では割れません'],forbidden=['結果：']),
 dict(id='schedule_absent',category='事実と未確認',turns=['今日の予定は？'],required=['計画はありません'],forbidden=['朝の運動','午後の読書']),
 dict(id='source_absent',category='出典',turns=['その出典は？'],required=['出典は確認できません'],forbidden=['https://']),
 dict(id='weather_place',category='不足情報',turns=['明後日の天気は？'],required=['市区町村'],forbidden=['最高気温：']),
 dict(id='weather_day_followup',category='会話文脈',turns=['明日の天気は？','明後日は？'],required=['明後日','市区町村'],forbidden=['今日の予報']),
 dict(id='search_to_calc',category='話題の切替',turns=['Googleで調べて','計算: 5*6'],required=['結果：30'],forbidden=['検索画面を']),
 dict(id='cancel_source',category='文脈の解除',turns=['キャンセル','その出典は？'],required=['出典は確認できません'],forbidden=['https://']),
 dict(id='past_empty',category='過去と現在',turns=['2000年1月1日の予定は？'],required=['2000-01-01','計画はありません'],forbidden=['今日の計画（']),
]
# These require actual model responses and human evidence review; no mock pass grades.
MODEL_CASES=[
 dict(id='analysis_missing_data',question='売上が下がった。広告費を倍にすべき？',criteria=['減少原因を決めつけない','期間・売上・費用など必要な情報を挙げる','追加情報なしに倍増が最適と断定しない']),
 dict(id='analysis_causation',question='新しい手順にしたらミスが減った。この手順のおかげと断定できる？',criteria=['相関と因果を区別する','件数や作業量など他の変化を確認する','断定を避け検証方法を提案する']),
 dict(id='conversation_humor',question='少し休憩して雑談しよう。',criteria=['自然で簡潔に返す','冗談がなくても合格','過剰な称賛・能力の誇張・不自然な決めぜりふを避ける']),
]

def run(output_dir=None):
    root=Path(__file__).resolve().parent
    entry=(root/'tomeris_desktop.py').read_text(encoding='utf-8')
    module=re.search(r'from (tomeris_desktop_v\d+) import main',entry)[1]
    service_class=importlib.import_module(module).DesktopService
    parent=root.parent/'work'/'v07';parent.mkdir(parents=True,exist_ok=True)
    records=[]
    # Any unexpected network or model generation fails the case, never quietly mocks success.
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden in offline evaluation')),patch('tomeris_capabilities.LocalProvider.generate',side_effect=AssertionError('model forbidden in offline evaluation')):
        for case in CASES:
            start=time.perf_counter();answers=[];error=None
            with tempfile.TemporaryDirectory(dir=parent) as folder:
                service=service_class(Path(folder),demo=True)
                try:
                    for question in case['turns']:answers.append(service.web_chat(question,'unused',automatic=True))
                except Exception as exc:error=type(exc).__name__+': '+str(exc)
                finally:service.close()
            answer=answers[-1] if answers else ''
            passed=error is None and all(t in answer for t in case['required']) and not any(t in answer for t in case['forbidden'])
            records.append(dict(**case,status='passed' if passed else 'failed',answers=answers,error=error,seconds=round(time.perf_counter()-start,4)))
    stamp=datetime.now(timezone.utc)
    result=dict(suite='tomeris_behavior_v1',created_at=stamp.isoformat(),app_module=module,app_sha256=hashlib.sha256((root/(module+'.py')).read_bytes()).hexdigest(),cases=records,model_cases=[dict(**c,status='not_evaluated') for c in MODEL_CASES],limits='固定のオフライン動作検査。実検索の品質・モデルの理解力・学習効果は測定していません。時間はテスト処理時間です。')
    output=Path(output_dir) if output_dir else root/'evaluations';output.mkdir(parents=True,exist_ok=True)
    path=output/('behavior_'+stamp.strftime('%Y%m%dT%H%M%S_%fZ')+'.json')
    with path.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    passed=sum(r['status']=='passed' for r in records)
    report=f'# 固定動作の評価\n\n対象：{module}\n\n合格 {passed}/{len(records)}。実モデルを要する3問は未評価。\n\n'+result['limits']+'\n\n'
    report+='\n'.join(f"- {r['id']}：{r['status']}" for r in records)
    path.with_suffix('.md').write_text(report+'\n',encoding='utf-8')
    print(f'{passed}/{len(records)} offline checks passed; {len(MODEL_CASES)} model cases NOT evaluated. {path}')
    return result

if __name__=='__main__':
    result=run()
    raise SystemExit(0 if all(c['status']=='passed' for c in result['cases']) else 1)
