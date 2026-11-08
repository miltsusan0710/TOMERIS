from pathlib import Path
out = Path('outputs')
app = (out/'tomeris_v06.py').read_text(encoding='utf-8')
app = app.replace('TOMERIS v0.6', 'TOMERIS v0.7').replace('トメリス v0.6', 'トメリス v0.7')
app = app.replace('tomeris_memory_v06.json', 'tomeris_memory_v07.json')
app = app.replace('from tomeris_pc_info_v06 import pc_info', 'from tomeris_pc_info_v06 import pc_info\nfrom tomeris_gemini_v07 import GeminiProvider, DEFAULT_MODEL')
app = app.replace('  /pc               ', '  /provider ollama  Ollamaへ切替（既定）\n  /provider gemini  Geminiへ切替（送信前に毎回確認）\n  /gemini-key       APIキーを非表示で入力（保存なし）\n  /pc               ')
app = app.replace('  /test             Ollamaへの接続確認', '  /test             選択中AIの確認（Geminiはキー設定のみ）')
app = app.replace('answer = provider.generate(build_messages(store, text))', 'answer = provider.generate([{ "role": "user", "content": text }] if getattr(provider, "cloud", False) else build_messages(store, text))')
app = app.replace('messages = build_messages(store, text)\n    for attempt in range(2):', 'messages = [{"role": "user", "content": text}] if getattr(provider, "cloud", False) else build_messages(store, text)\n    for attempt in range(1 if getattr(provider, "cloud", False) else 2):')
app = app.replace('parser.add_argument("--pc-info",', 'parser.add_argument("--gemini-model", default=DEFAULT_MODEL, help="利用可能なGeminiモデルID")\n    parser.add_argument("--pc-info",')
app = app.replace('    provider = OllamaProvider(model=MODEL_NAME, base_url=OLLAMA_URL)', '    local_provider = OllamaProvider(model=MODEL_NAME, base_url=OLLAMA_URL)\n    provider = local_provider\n    gemini_provider = None')
app = app.replace('読み取り専用PC情報・回答検証版', 'Ollama / Gemini切替・PC情報版')
app = app.replace('        if text == "/pc":', '''        if text.startswith("/provider"):
            if text == "/provider ollama":
                provider = local_provider
                print("Ollamaへ切り替えました（ローカル）。")
            elif text == "/provider gemini":
                try:
                    if gemini_provider is None:
                        gemini_provider = GeminiProvider(args.gemini_model)
                    provider = gemini_provider
                    print("Geminiへ切り替えました。記憶・過去会話は送信しません。質問ごとに送信確認があります。")
                    print(provider.check()[1])
                except ProviderError as exc:
                    print(str(exc))
            else:
                print("使い方: /provider ollama または /provider gemini")
            continue
        if text == "/gemini-key":
            try:
                if gemini_provider is None:
                    gemini_provider = GeminiProvider(args.gemini_model)
                gemini_provider.enter_key()
            except ProviderError as exc:
                print(str(exc))
            continue
        if text == "/pc":''')
app = app.replace('print(f"トメリス：{MODEL_NAME} / {OLLAMA_URL}（ローカル）"); continue', 'print(f"トメリス：Gemini / {provider.model}（Google API）" if getattr(provider, "cloud", False) else f"トメリス：{MODEL_NAME} / {OLLAMA_URL}（ローカル）"); continue')
app = app.replace("{'接続成功' if ok else '接続失敗'}", "{'確認OK' if ok else '要確認'}")
app = app.replace('ファイル変更・削除・実行・外部送信は行わない。', 'PCへの変更・削除・実行は行わない。Geminiへの質問送信は本文確認後のみ行う。')
app = app.replace('トメリス v0.5.1 | 回答品質のチェック', 'トメリス v0.7 | 回答品質のチェック（Geminiは再送せず定型へ切替）')
(out/'tomeris_v07.py').write_text(app, encoding='utf-8')
for src, dest in [('test_tomeris_v06.py','test_v07_pc_regression.py'), ('test_v051_regression.py','test_v07_guardrail_regression.py')]:
    tests = (out/src).read_text(encoding='utf-8').replace('import tomeris_v06 as app', 'import tomeris_v07 as app')
    (out/dest).write_text(tests, encoding='utf-8')
