from pathlib import Path

source = Path(r'C:\Users\hiroy\OneDrive\デスクトップ\tomeris_v01')
out = Path('outputs')
standalone = (out / 'tomeris_v06.py').read_text(encoding='utf-8')
pc_module = standalone[:standalone.index('\ndef chat(')]
pc_module = pc_module.replace('"""Tomeris v0.6 standalone. Python 3.10+, standard library only.\n\nExisting source was unavailable: no legacy files or persistent memory are read/written.\n"""', '"""Fixed read-only PC metrics. No network, file contents, or persistence."""')
pc_module = pc_module.replace('import argparse\n', '').replace('import json\n', '').replace('import urllib.request\n', '')
(out / 'tomeris_pc_info_v06.py').write_text(pc_module, encoding='utf-8')
for name in ('tomeris_memory_engine.py', 'tomeris_provider.py', 'tomeris_guardrails.py', 'tomeris_core.md'):
    (out / name).write_bytes((source / name).read_bytes())
app = (source / 'tomeris_v051.py').read_text(encoding='utf-8')
app = app.replace('"""TOMERIS v0.5.1 — response validation and no PC execution rights."""', '"""TOMERIS v0.6 — v0.5.1 plus explicit read-only PC metrics."""')
app = app.replace('import re\n', 'import re\nimport argparse\nimport json\nfrom tomeris_pc_info_v06 import pc_info\n')
app = app.replace('APP_DIR / "tomeris_memory.json"', 'APP_DIR / "tomeris_memory_v06.json"')
app = app.replace('  /help             コマンド一覧', '  /pc               PC基本情報を画面表示（AI送信・記憶保存なし）\n  /help             コマンド一覧')
app = app.replace('TOMERIS v0.5.1 | 回答検証・実行宣言防止版', 'TOMERIS v0.6 | 読み取り専用PC情報・回答検証版')
app = app.replace('"PCを操作する機能は未実装です。', '"PC情報は /pc コマンドでのみ取得します。あなたには取得結果を渡していません。参照・診断したと主張しないでください。PCを変更する機能は未実装です。')
app = app.replace('def main() -> int:\n    try:', '''def import_memory(source: Path, destination: Path) -> None:
    """Explicit one-time import; never overwrite an existing destination."""
    raw = source.read_bytes()
    loaded = json.loads(raw.decode("utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("記憶はJSONオブジェクトである必要があります")
    with destination.open("xb") as target:
        target.write(raw)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="トメリス v0.6")
    parser.add_argument("--pc-info", action="store_true", help="記憶・AIに接続せずPC情報を表示")
    parser.add_argument("--import-memory", type=Path, help="旧記憶をv0.6専用ファイルへ初回だけ複製")
    args = parser.parse_args([] if argv is None else argv)
    if args.pc_info:
        print(json.dumps(pc_info(), ensure_ascii=False, indent=2))
        return 0
    if args.import_memory:
        try:
            import_memory(args.import_memory, MEMORY_FILE)
        except (OSError, ValueError, UnicodeError) as exc:
            print(f"記憶の複製を中止しました。既存の保存先は上書きしません: {exc}")
            return 2
    try:''')
app = app.replace('if text == "/help":', '''if text == "/pc":
            print(json.dumps(pc_info(), ensure_ascii=False, indent=2))
            continue
        if text.startswith("/pc"):
            print("使い方: /pc （引数は受け付けません）")
            continue
        if text == "/help":''')
app = app.replace('"トメリス：PC操作の安全基準（現段階では方針表示のみ）\\n"', '"トメリス：PC操作の安全基準（PC情報表示のみ実装）\\n"\n                "PC情報取得: /pc。結果は画面のみ。AI送信・記憶保存はしません。\\n"')
app = app.replace('raise SystemExit(main())', 'raise SystemExit(main(sys.argv[1:]))')
(out / 'tomeris_v06.py').write_text(app, encoding='utf-8')
tests = (source / 'test_tomeris_v051.py').read_text(encoding='utf-8').replace('import tomeris_v051 as app', 'import tomeris_v06 as app')
(out / 'test_v051_regression.py').write_text(tests, encoding='utf-8')
