from pathlib import Path
out=Path('outputs')
code=(out/'tomeris_compare_v08.py').read_text(encoding='utf-8-sig')
# Keep transport in v0.8 untouched; new comparison uses the focused local provider.
start=code.index('class NoRedirect(')
end=code.index('\ndef list_models(')
code=code[:start]+'from tomeris_advice_v081 import AdviceProvider as LocalProvider\n\n'+code[end:]
code=code.replace("'error':'取得失敗'", "'error':'取得失敗'")
(out/'tomeris_compare_v081.py').write_text(code,encoding='utf-8')
app=(out/'tomeris_v08.py').read_text(encoding='utf-8-sig')
app=app.replace('v0.8','v0.8.1').replace('tomeris_memory_v08.json','tomeris_memory_v081.json')
app=app.replace('from tomeris_compare_v08 import','from tomeris_compare_v081 import')
app=app.replace('from tomeris_gemini_v07 import GeminiProvider, DEFAULT_MODEL','from tomeris_gemini_v07 import GeminiProvider, DEFAULT_MODEL\nfrom tomeris_advice_v081 import DIRECT_RULES')
app=app.replace('"最後に『追加を実行する』『操作します』とは書かず、未実行であることを明示してください。"','"操作を実行したと宣言しないでください。普通の助言では操作状態の定型文は不要です。"')
app=app.replace('"リスクや安全性の質問では、指定数を守り、各項目を「リスク／起こり得る影響／具体的な対策／実行前の確認」に分けてください。"','"PC操作のリスクや安全性を聞かれた場合に限り、各項目にリスク・影響・具体策・実行前の確認を含めてください。"')
app=app.replace('messages: list[dict[str, str]] = [{"role": "system", "content": system}]','messages: list[dict[str, str]] = [{"role": "system", "content": system + "\\n" + DIRECT_RULES}]')
app=app.replace('ローカルAI回答比較・PC情報版','質問への直接回答・具体策改善版')
app=app.replace('        "- 注意: 自動検査', '        "- ローカルの工夫・コツ・方法・具体策: 項目数と一部の話題ずれを検査し、必要なら1回再生成\\n"\n        "- 注意: 自動検査')
(out/'tomeris_v081.py').write_text(app,encoding='utf-8')
for name in ['test_v08_pc_regression.py','test_v08_guardrail_regression.py','test_v08_gemini.py','test_v08_compare.py']:
    code=(out/name).read_text(encoding='utf-8-sig').replace('import tomeris_v08 as app','import tomeris_v081 as app').replace('import tomeris_compare_v08 as cmp','import tomeris_compare_v081 as cmp')
    (out/name.replace('v08','v081')).write_text(code,encoding='utf-8')
