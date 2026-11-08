from pathlib import Path
out=Path('outputs')
code=(out/'tomeris_advice_v081.py').read_text(encoding='utf-8-sig')
code=code.replace("    '例：集中の工夫なら「通知を切り、25分間は1つの作業だけに取り組む」のように書きます。'\n    '例を無関係な質問へ流用せず、質問の目的に合わせてください。'", "    '一般的な助言は各項目1〜2文で簡潔に書き、不要な前置きやまとめを省いてください。'\n    '効果を必ず得られると断言せず、個人差のある方法は試す選択肢として示してください。'\n    '根拠のない専門用語、独自の方法名、出典や研究結果を作らないでください。'\n    '確信がない名称は使わず、実際に行う手順を平易な言葉で説明してください。'\n    '質問に「今日」「今すぐ」があれば、その場で着手できる行動を優先してください。'\n    '睡眠や生活全般の改善だけで終わらず、現在の作業で行う手順を答えてください。'")
code=code.replace("    return issues\n", """    # Caution on newly introduced labels; this does not establish truth or falsity.
    label = re.search(r'[「『]([^」』]{2,40})[」』]\\s*(?:と呼|という(?:方法|手法|時間管理法))', answer)
    if label and label.group(1) not in question:
        issues.append('新しい方法名を付けず平易な手順で説明する（名称の根拠は未確認）')
    if not any(word in question for word in ('詳しく','詳細','長文')) and len(answer) > 600:
        issues.append('各項目1〜2文を目安に短くする')
    return issues
""")
(out/'tomeris_advice_v082.py').write_text(code,encoding='utf-8')
code=(out/'tomeris_compare_v081.py').read_text(encoding='utf-8-sig').replace('tomeris_advice_v081','tomeris_advice_v082')
(out/'tomeris_compare_v082.py').write_text(code,encoding='utf-8')
app=(out/'tomeris_v081.py').read_text(encoding='utf-8-sig').replace('v0.8.1','v0.8.2').replace('tomeris_memory_v081.json','tomeris_memory_v082.json').replace('tomeris_compare_v081','tomeris_compare_v082').replace('tomeris_advice_v081','tomeris_advice_v082')
app=app.replace('質問への直接回答・具体策改善版','短い具体策・不確かな名称の抑制版')
app=app.replace('項目数と一部の話題ずれを検査','項目数・一部の話題ずれ・新しい名称・長さを簡易検査')
(out/'tomeris_v082.py').write_text(app,encoding='utf-8')
for src in out.glob('test_v081*.py'):
    code=src.read_text(encoding='utf-8-sig').replace('tomeris_v081','tomeris_v082').replace('tomeris_advice_v081','tomeris_advice_v082').replace('tomeris_compare_v081','tomeris_compare_v082')
    (out/src.name.replace('v081','v082')).write_text(code,encoding='utf-8')
