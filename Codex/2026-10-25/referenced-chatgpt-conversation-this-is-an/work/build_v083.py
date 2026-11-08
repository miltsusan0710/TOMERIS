from pathlib import Path
out=Path('outputs')
code=(out/'tomeris_advice_v082.py').read_text(encoding='utf-8-sig')
start=code.index('DIRECT_RULES = (')
end=code.index('\n\ndef practical_request')
code=code[:start]+'from tomeris_context_v083 import SHORT_RULES as DIRECT_RULES\n'+code[end:]
code=code.replace("prepared=[{'role':'system','content':DIRECT_RULES}]+messages",'prepared=list(messages)')
code=code.replace("revised=[{'role':'system','content':DIRECT_RULES+' 修正事項：'+'。'.join(issues)}]+messages", "revised=[{'role':'system','content':'修正事項：'+'。'.join(issues)}]+messages")
(out/'tomeris_advice_v083.py').write_text(code,encoding='utf-8')
code=(out/'tomeris_compare_v082.py').read_text(encoding='utf-8-sig').replace('tomeris_advice_v082','tomeris_advice_v083')
(out/'tomeris_compare_v083.py').write_text(code,encoding='utf-8')
app=(out/'tomeris_v082.py').read_text(encoding='utf-8-sig').replace('v0.8.2','v0.8.3').replace('tomeris_memory_v082.json','tomeris_memory_v083.json').replace('tomeris_compare_v082','tomeris_compare_v083').replace('tomeris_advice_v082','tomeris_advice_v083')
app=app.replace('from tomeris_advice_v083 import DIRECT_RULES','from tomeris_context_v083 import build_short_messages')
start=app.index('def build_messages(')
end=app.index('\ndef generate_checked_response',start)
app=app[:start]+'''def build_messages(store: MemoryStore, user_text: str) -> list[dict[str, str]]:
    return build_short_messages(store, user_text, is_risk=is_pc_risk_question(user_text), core_supplier=read_core)

'''+app[end:]
app=app.replace('短い具体策・不確かな名称の抑制版','短い指示・必要時のみ記憶参照版')
app=app.replace('  /models           ','  /ask-memory 質問  記憶を参照して回答（ローカル）\n  /models           ',1)
app=app.replace('        should_save = True', '''        if text == "/ask-memory" or text.startswith("/ask-memory "):
            query = text[len("/ask-memory"):].strip()
            if not query:
                print("使い方: /ask-memory 質問")
                continue
            if getattr(provider, "cloud", False) is True:
                print("記憶を使う質問は /provider ollama に切り替えてください。")
                continue
            text = "記憶を参照して：" + query
        should_save = True''')
(out/'tomeris_v083.py').write_text(app,encoding='utf-8')
for src in out.glob('test_v082*.py'):
    code=src.read_text(encoding='utf-8-sig').replace('tomeris_v082','tomeris_v083').replace('tomeris_advice_v082','tomeris_advice_v083').replace('tomeris_compare_v082','tomeris_compare_v083')
    (out/src.name.replace('v082','v083')).write_text(code,encoding='utf-8')
