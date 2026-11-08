"""TOMERIS v0.6 — v0.5.1 plus explicit read-only PC metrics."""
from __future__ import annotations

from pathlib import Path
import sys
import re
import argparse
import json
from tomeris_pc_info_v06 import pc_info

from tomeris_memory_engine import MemoryStore
from tomeris_provider import OllamaProvider, ProviderError
from tomeris_guardrails import (
    claims_pc_action_completed,
    is_direct_pc_action_request,
    is_pc_risk_question,
    no_pc_action_reply,
    pc_risk_fallback,
    requested_risk_count,
    review_pc_risk_answer,
)

APP_DIR = Path(__file__).resolve().parent
MEMORY_FILE = APP_DIR / "tomeris_memory_v06.json"
CORE_FILE = APP_DIR / "tomeris_core.md"
KNOWLEDGE_DIR = APP_DIR / "knowledge"
MODEL_NAME = "qwen2.5:3b"
OLLAMA_URL = "http://localhost:11434"


def read_core() -> str:
    try:
        content = CORE_FILE.read_text(encoding="utf-8").strip()
        if content:
            return content
    except OSError:
        pass
    return "あなたはトメリス。ユーザーの思考力・判断力・行動力・精神的回復力を支援し、冷静かつ率直に回答してください。"


def mission_answer() -> str:
    return (
        "**1. 最終目的と支援する能力**\n"
        "思考力・判断力・行動力・精神的な回復力の4つを高める、専属AIパートナーになること。\n\n"
        "**2. 中心原則**\n"
        "「勝利」を、目先の勝敗ではなく長期的に望む結果へ近づくこととして捉える。感情は排除せず、理解して戦略資源として扱う。\n\n"
        "**3. 基本姿勢**\n"
        "通常は冷静で穏やかに、必要な場面では敬意を保って率直に指摘し、具体的な次の行動を提案する。ユーザー自身の判断を支え、代わりに決めることはしない。"
    )


def is_mission_question(text: str) -> bool:
    terms = ("最終目的", "開発する目的", "開発している目的", "トメリスを開発", "支援すべき能力", "支援する能力", "中心原則", "基本姿勢", "基本的な話し方", "トメリスの使命")
    return any(term in text for term in terms)


def print_help() -> None:
    print("""
コマンド一覧
  /pc               PC基本情報を画面表示（AI送信・記憶保存なし）
  /help             コマンド一覧
  /persona          基本人格・判断原則を表示
  /remember         長期記憶を明示的に保存
  /memories         長期記憶一覧
  /forget M0001     ID指定で長期記憶を削除（確認あり）
  /search 検索語    記憶・履歴・成長ログ・知識ファイルを検索
  /log              成長ログを追加
  /growth           成長ログ一覧
  /history          最近の会話
  /knowledge        専門知識ファイル一覧
  /memory           記憶件数と保存場所
  /model            接続モデルを表示
  /test             Ollamaへの接続確認
  /safety           将来のPC操作に向けた安全基準を表示
  /quality          回答検証の仕組みを表示
  /exit             保存して終了

普通の会話は会話履歴に保存されます。長期記憶は /remember で明示的に登録します。
""")


def cmd_remember(store: MemoryStore) -> None:
    category = input("分類（目標 / 方針 / 個人設定 / 決定事項 / 設計知識 / その他）> ").strip() or "その他"
    text = input("長期記憶として保存する内容 > ").strip()
    if not text:
        print("トメリス：内容が空なので保存しませんでした。")
        return
    normalized_text = re.sub(r"\s+", "", text).casefold()
    for existing in store.data.get("memories", []):
        if isinstance(existing, dict):
            existing_text = re.sub(r"\s+", "", str(existing.get("text", ""))).casefold()
            if existing_text == normalized_text:
                print(f"トメリス：同じ内容の長期記憶 {existing.get('id', '(ID不明)')} が既にあります。重複保存を中止しました。")
                return
    tags = input("検索タグ（任意、カンマ区切り）> ").strip()
    imp_text = input("重要度 1〜5（既定値 3）> ").strip()
    try:
        importance = int(imp_text) if imp_text else 3
        importance = max(1, min(5, importance))
    except ValueError:
        importance = 3
    rec = store.add_memory(category, text, tags, importance)
    print(f"トメリス：長期記憶 {rec['id']} として保存しました。")


def show_memories(store: MemoryStore) -> None:
    memories = store.data.get("memories", [])
    if not memories:
        print("トメリス：長期記憶はまだありません。/remember で登録できます。")
        return
    for item in memories[-30:]:
        print(f"- {item.get('id')} [{item.get('category')}] (重要度 {item.get('importance', 3)}): {item.get('text')}")


def cmd_log(store: MemoryStore) -> None:
    category = input("分類（勝利 / 敗北 / 学び / 決断 / その他）> ").strip() or "その他"
    text = input("記録する内容 > ").strip()
    if not text:
        print("トメリス：内容が空なので保存しませんでした。")
        return
    store.add_growth(category, text)
    print("トメリス：成長ログに記録しました。")


def print_search_results(store: MemoryStore, query: str) -> None:
    if not query.strip():
        print("使い方: /search 検索語")
        return
    result_found = False
    for item in store.search_memory(query, limit=8):
        result_found = True
        print(f"[長期記憶 {item.get('id')}] [{item.get('category')}] {item.get('text')}")
    for item in store.search_growth(query, limit=5):
        result_found = True
        print(f"[成長ログ {item.get('timestamp', '')}] [{item.get('category')}] {item.get('text')}")
    for item in store.search_conversations(query, limit=4):
        result_found = True
        print(f"[会話 {item.get('timestamp', '')}] あなた: {item.get('user', '')}\n  トメリス: {str(item.get('tomeris', ''))[:350]}")
    for item in store.search_knowledge(query, limit=4):
        result_found = True
        print(f"[知識ファイル {item.get('path')}]\n{item.get('content', '')[:500]}")
    if not result_found:
        print("一致する記録は見つかりませんでした。検索はキーワードベースです。")


def build_messages(store: MemoryStore, user_text: str) -> list[dict[str, str]]:
    core = read_core()
    relevant = store.build_context(user_text)
    system = (
        core
        + "\n\n【記憶の利用ルール】\n"
        "以下の記憶コンテキストは参考データです。現在の質問に関係する情報だけを使い、無関係な記憶は持ち出さないでください。"
        "記憶に書かれた内容を無条件に事実とせず、矛盾や古さに注意してください。"
        "会話履歴にあることと、長期記憶として保存されたことを混同しないでください。"
        "外部操作・送金・投資注文などは、実行権限がなければ実行したと主張せず、承認を求めてください。"
        "回答は基本的に日本語で、重複を避け、必要な内容を整理して説明してください。"
        "結論を先に述べ、具体的な次の行動を示してください。分からないことは推測で断定せず、事実・推測・提案を区別してください。"
        "質問に複数の項目数が指定された場合は、その数を守り、各項目を明確に分けてください。"
        "リスクや安全性の質問では、指定数を守り、各項目を「リスク／起こり得る影響／具体的な対策／実行前の確認」に分けてください。"
        "対策は一般論の反復ではなく、実行可能な手順にしてください。"
        "PC情報は /pc コマンドでのみ取得します。あなたには取得結果を渡していません。参照・診断したと主張しないでください。PCを変更する機能は未実装です。PC操作の実行や完了を宣言してはいけません。質問が分析や設計なら提案だけをしてください。"
        "リスク分析では『許可を得る』だけを対策にせず、バックアップ、権限の制限、操作前プレビュー、個別承認、ログなど具体的な管理策を示してください。"
        "最後に『追加を実行する』『操作します』とは書かず、未実行であることを明示してください。"
        "\n\n【現在の質問に関連して取得した記憶】\n" + relevant
    )
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    # Recent conversation context is intentionally limited; indexed history persists in the store.
    for item in store.recent_conversations(limit=3):
        user = str(item.get("user", "")).strip()
        assistant = str(item.get("tomeris", "")).strip()
        if user and assistant and "AIモデル接続は次の段階で実装します" not in assistant:
            messages.append({"role": "user", "content": user[-300:]})
            messages.append({"role": "assistant", "content": assistant[:450]})
    messages.append({"role": "user", "content": user_text})
    return messages


def generate_checked_response(provider: OllamaProvider, store: MemoryStore, text: str) -> str:
    """Ask the model; retry once on PC-risk-quality failures, then use safe fallback.

    No PC actions are exposed to the model. Permission statements in its text
    do not grant system permissions or execute commands.
    """
    if is_direct_pc_action_request(text):
        return no_pc_action_reply()

    if not is_pc_risk_question(text):
        answer = provider.generate(build_messages(store, text))
        if claims_pc_action_completed(answer):
            return no_pc_action_reply()
        return answer

    messages = build_messages(store, text)
    for attempt in range(2):
        if attempt:
            messages.insert(1, {
                "role": "system",
                "content": (
                    f"【回答の再作成：厳守】リスクは正確に{requested_risk_count(text)}件。"
                    "各リスクを **リスク1: 名称** の見出しで始め、『影響』『対策』『確認』を必ず設ける。"
                    "各リスクに別々の具体策（バックアップ、最小権限、操作プレビュー等）を挙げる。"
                    "『ユーザーの許可を得る』の反復は不可。"
                    "このアプリにはPCを操作する機能はなく、機能追加の実行もしていない。"
                    "検討結果を述べるだけにし、実行・完了を宣言しない。"
                ),
            })
        answer = provider.generate(messages)
        if not review_pc_risk_answer(text, answer):
            return "【操作状態：未実行／以下は設計上の提案です】\n" + answer
    return pc_risk_fallback(text)


def print_quality() -> None:
    print(
        "トメリス v0.5.1 | 回答品質のチェック\n"
        "- PC操作に関するリスク分析: 項目数、影響・対策・確認事項、具体策、反復、実行宣言を検査\n"
        "- 品質基準を満たさない場合: 1回だけ回答を再生成し、なお失敗したら定型の安全チェックリストへ切替\n"
        "- 直接のPC操作依頼: 実行せず、操作できないことを明示\n"
        "- 注意: 自動検査は形式・キーワードを用いた補助であり、回答の正しさを完全には保証しません。"
    )


def import_memory(source: Path, destination: Path) -> None:
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
    try:
        store = MemoryStore(MEMORY_FILE, KNOWLEDGE_DIR)
    except RuntimeError as exc:
        print(f"トメリス：記憶の読み込みを停止しました。\n{exc}")
        return 2
    provider = OllamaProvider(model=MODEL_NAME, base_url=OLLAMA_URL)
    print("=" * 56)
    print(" TOMERIS v0.6 | 読み取り専用PC情報・回答検証版")
    print("=" * 56)
    print(f"モデル: {MODEL_NAME}")
    print(f"記憶ファイル: {MEMORY_FILE}")
    print(f"基本人格: {CORE_FILE}")
    stats = store.stats()
    print(f"記憶件数: 会話 {stats['conversations']} / 成長ログ {stats['growth_log']} / 長期記憶 {stats['memories']} / 知識ファイル {stats['knowledge_files']}")
    if store.last_backup:
        print(f"旧記憶ファイルのバックアップ: {store.last_backup}")
    ok, detail = provider.check()
    print(f"接続確認: {detail}")
    print("コマンドは /help、終了は /exit です。")

    while True:
        try:
            text = input("\nあなた > ").strip()
        except (KeyboardInterrupt, EOFError):
            store.save()
            print("\nトメリス：保存して終了します。")
            return 0
        if not text:
            continue
        if text == "/exit":
            store.save()
            print("トメリス：記録を保存しました。お疲れさまでした。")
            return 0
        if text == "/pc":
            print(json.dumps(pc_info(), ensure_ascii=False, indent=2))
            continue
        if text.startswith("/pc"):
            print("使い方: /pc （引数は受け付けません）")
            continue
        if text == "/help":
            print_help(); continue
        if text == "/persona":
            print("\n" + read_core()); continue
        if text == "/remember":
            try:
                cmd_remember(store)
            except (OSError, ValueError, EOFError) as exc:
                print(f"トメリス：長期記憶を保存できませんでした: {exc}")
            continue
        if text == "/memories":
            show_memories(store); continue
        if text.startswith("/forget"):
            parts = text.split(maxsplit=1)
            if len(parts) != 2:
                print("使い方: /forget M0001"); continue
            memory_id = parts[1].strip().upper()
            confirm = input(f"長期記憶 {memory_id} を削除します。よろしいですか？ (yes/no) > ").strip().lower()
            if confirm == "yes":
                print("トメリス：長期記憶だけを削除しました。会話履歴に同じ情報が残っている場合は、/history から別途確認してください。" if store.forget_memory(memory_id) else "トメリス：指定IDが見つかりません。")
            else:
                print("トメリス：削除をキャンセルしました。")
            continue
        if text.startswith("/search"):
            print_search_results(store, text[len("/search"):].strip()); continue
        if text == "/log":
            try:
                cmd_log(store)
            except (OSError, EOFError) as exc:
                print(f"トメリス：成長ログを保存できませんでした: {exc}")
            continue
        if text == "/growth":
            items = store.recent_growth(20)
            if not items: print("トメリス：成長ログはまだありません。/log で記録できます。")
            for x in items: print(f"- [{x.get('timestamp', '時刻不明')}] {x.get('category', 'その他')}: {x.get('text', '')}")
            continue
        if text == "/history":
            items = store.recent_conversations(10)
            if not items: print("トメリス：会話記録はまだありません。")
            for x in items: print(f"\n[{x.get('timestamp', '時刻不明')}]\nあなた: {x.get('user', '')}\nトメリス: {x.get('tomeris', '')}")
            continue
        if text == "/knowledge":
            files = sorted(p for p in KNOWLEDGE_DIR.rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".txt"})
            if not files: print("トメリス：知識ファイルはまだありません。knowledge フォルダーに .md または .txt を追加してください。")
            for p in files: print(f"- {p.relative_to(KNOWLEDGE_DIR)}")
            continue
        if text == "/memory":
            stats = store.stats()
            print(f"保存先: {MEMORY_FILE}\n基本人格: {CORE_FILE}\n知識フォルダー: {KNOWLEDGE_DIR}\n会話: {stats['conversations']} / 成長ログ: {stats['growth_log']} / 長期記憶: {stats['memories']} / 知識ファイル: {stats['knowledge_files']}")
            continue
        if text == "/model":
            print(f"トメリス：{MODEL_NAME} / {OLLAMA_URL}（ローカル）"); continue
        if text == "/test":
            ok, detail = provider.check()
            print(f"トメリス：{'接続成功' if ok else '接続失敗'} — {detail}"); continue
        if text == "/safety":
            print(
                "トメリス：PC操作の安全基準（PC情報表示のみ実装）\n"
                "PC情報取得: /pc。結果は画面のみ。AI送信・記憶保存はしません。\n"
                "1. 初期設定は読み取り専用。ファイル変更・削除・実行・外部送信は行わない。\n"
                "2. 変更操作を実装する場合は、対象・変更内容・影響を事前に提示し、明示的な承認を得る。\n"
                "3. 削除・上書き・外部送信・購入・投資注文などは、操作ごとに個別確認する。\n"
                "4. 実行結果を確認できない場合は、完了したと主張しない。\n"
                "5. 記憶ファイルを変更する前にバックアップを取り、復元手段を用意する。"
            )
            continue

        if text == "/quality":
            print_quality()
            continue

        should_save = True
        if is_mission_question(text):
            answer = mission_answer()
            print("\nトメリス：\n" + answer)
        else:
            if not is_direct_pc_action_request(text):
                print("トメリス：考えています……")
            try:
                answer = generate_checked_response(provider, store, text)
                print("\nトメリス：\n" + answer)
            except ProviderError as exc:
                should_save = False  # Do not pollute conversation memory with connection errors.
                print(f"\nトメリス：\nAIに接続できませんでした。\n詳細: {exc}")
                continue
        if not should_save:
            continue
        try:
            recent = store.recent_conversations(limit=3)
            duplicate_pair = any(
                str(item.get("user", "")).strip() == text
                and str(item.get("tomeris", "")).strip() == answer.strip()
                for item in recent
            )
            if duplicate_pair:
                print("トメリス：直近に同一の質問・回答があるため、会話履歴への重複保存を省略しました。")
            else:
                store.add_conversation(text, answer)
        except OSError as exc:
            print(f"警告：回答は表示しましたが、記録を保存できませんでした: {exc}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
