from pathlib import Path
out=Path('outputs')
code=(out/'tomeris_context_v083.py').read_text(encoding='utf-8-sig')
code=code.replace("context['長期記憶']=[str(x.get('text',''))[:220] for x in memories if isinstance(x,dict)]", "context['長期記憶']=[{'id':str(x.get('id',''))[:20], '分類':str(x.get('category',''))[:30], '原文':str(x.get('text',''))[:220]} for x in memories if isinstance(x,dict)]")
code=code.replace('不明な過去情報を推測せず、関連分だけ使用する。','不明な過去情報を推測せず、関連分だけ使用する。原文の主語を保つ。目標の分類だけでユーザー本人の目標と判断しない。トメリスの役割とユーザーの目標を区別し、判断原則を成果の保証に言い換えない。')
(out/'tomeris_context_v084.py').write_text(code,encoding='utf-8')
for src,dst in [('tomeris_advice_v083.py','tomeris_advice_v084.py'),('tomeris_compare_v083.py','tomeris_compare_v084.py'),('tomeris_v083.py','tomeris_v084.py')]:
    code=(out/src).read_text(encoding='utf-8-sig').replace('v0.8.3','v0.8.4').replace('tomeris_memory_v083.json','tomeris_memory_v084.json').replace('tomeris_context_v083','tomeris_context_v084').replace('tomeris_advice_v083','tomeris_advice_v084').replace('tomeris_compare_v083','tomeris_compare_v084')
    if src=='tomeris_v083.py':
        code=code.replace('from tomeris_context_v084 import build_short_messages','from tomeris_context_v084 import build_short_messages\nfrom tomeris_recall_v084 import goal_recall')
        marker='    if not is_pc_risk_question(text):'
        code=code.replace(marker,'''    if getattr(provider, "cloud", False) is not True:
        recalled = goal_recall(store, text)
        if recalled is not None:
            return recalled

'''+marker,1)
        code=code.replace('短い指示・必要時のみ記憶参照版','目標の原文参照・主体の区別版')
    (out/dst).write_text(code,encoding='utf-8')
for src in out.glob('test_v083*.py'):
    code=src.read_text(encoding='utf-8-sig').replace('tomeris_v083','tomeris_v084').replace('tomeris_advice_v083','tomeris_advice_v084').replace('tomeris_compare_v083','tomeris_compare_v084').replace('tomeris_context_v083','tomeris_context_v084')
    (out/src.name.replace('v083','v084')).write_text(code,encoding='utf-8')
