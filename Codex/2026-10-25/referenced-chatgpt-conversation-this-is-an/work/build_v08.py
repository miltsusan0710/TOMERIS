from pathlib import Path
out=Path('outputs')
app=(out/'tomeris_v07.py').read_text(encoding='utf-8-sig')
app=app.replace('v0.7','v0.8').replace('tomeris_memory_v07.json','tomeris_memory_v08.json')
app=app.replace('from tomeris_provider import OllamaProvider, ProviderError','from tomeris_provider import ProviderError\nfrom tomeris_compare_v08 import LocalProvider as OllamaProvider, list_models, compare, display')
app=app.replace('  /provider ollama', '  /models           導入済みローカルモデル一覧\n  /compare A B 質問  2モデルの回答を比較（会話履歴とは別に保存）\n  /comparisons      最近の比較結果を表示\n  /provider ollama',1)
app=app.replace('旧記憶をv0.6専用ファイルへ初回だけ複製','旧記憶をv0.8専用ファイルへ初回だけ複製')
app=app.replace('Ollama / Gemini切替・PC情報版','ローカルAI回答比較・PC情報版')
app=app.replace('        if text.startswith("/provider"):', '''        if text == "/models":
            try:
                models = list_models(local_provider)
                print("導入済みローカルモデル:")
                for name in models:
                    print("- " + name)
                if len(models) < 2:
                    print("比較には異なる2モデルが必要です。モデルは自動追加しません。")
            except ProviderError as exc:
                print(str(exc))
            continue
        if text == "/comparisons":
            records = store.data.get("comparisons", [])
            if not records:
                print("比較記録はまだありません。")
            for record in records[-5:]:
                print("\\n質問: " + record["question"])
                display(record["results"])
            continue
        if text == "/compare" or text.startswith("/compare "):
            parts = text.split(maxsplit=3)
            if len(parts) != 4:
                print("使い方: /compare モデルA モデルB 質問")
                continue
            question = parts[3]
            try:
                # Freeze the same context before either model runs. Never call Gemini here.
                results = compare(parts[1:3], question, build_messages(store, question))
                display(results)
            except ProviderError as exc:
                print(str(exc))
                continue
            if any(item["status"] != "error" for item in results):
                records = store.data.setdefault("comparisons", [])
                records.append({"question": question, "results": results})
                try:
                    store.save()
                    print("比較専用の記録に保存しました。通常の会話履歴には追加しません。")
                except OSError:
                    records.pop()
                    print("比較は表示しましたが、保存できませんでした。")
            continue
        if text.startswith("/provider"):''')
(out/'tomeris_v08.py').write_text(app,encoding='utf-8')
for name in ['test_v07_pc_regression.py','test_v07_guardrail_regression.py','test_v07_gemini.py']:
    code=(out/name).read_text(encoding='utf-8-sig').replace('import tomeris_v07 as app','import tomeris_v08 as app')
    (out/name.replace('v07','v08')).write_text(code,encoding='utf-8')
