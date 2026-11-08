"""TOMERIS v0.5.1: text-only safety checks. No OS-control capability.

This module does not execute commands or access the user's files. It only
classifies user text, checks responses, and supplies safe fallback text.
"""
from __future__ import annotations

import re

_PC_WORDS = ("PC操作", "ＰＣ操作", "パソコン操作", "ファイル操作", "自動操作", "Windows操作", "デスクトップ操作")
_RISK_WORDS = ("リスク", "危険", "安全", "懸念", "問題点")
_ACTION_WORDS = (
    "削除して", "消去して", "上書きして", "移動して", "コピーして", "送信して", "起動して",
    "実行して", "インストールして", "ファイルを開いて", "操作して", "変更して", "書き換えて",
)
_TARGET_WORDS = ("PC", "パソコン", "Windows", "フォルダ", "ファイル", "アプリ", "メール", "ソフト", "プログラム", "データ")
_SPECIFIC_CONTROLS = (
    "バックアップ", "復元", "読み取り専用", "権限を限定", "権限を制限", "権限分離",
    "アクセス制限", "許可リスト", "ホワイトリスト", "差分", "プレビュー", "操作ログ",
    "監査ログ", "送信先", "対象ファイル", "対象フォルダ", "実行範囲", "対象範囲",
    "隔離", "サンドボックス", "ロールバック", "取り消し", "承認画面", "一件ずつ", "個別承認",
    "最小権限", "暗号化", "外部送信を禁止", "外部送信は禁止", "ネットワークアクセスを禁止",
)


def is_pc_risk_question(question: str) -> bool:
    text = question.casefold()
    return any(word.casefold() in text for word in _PC_WORDS) and any(word in text for word in _RISK_WORDS)


def is_direct_pc_action_request(question: str) -> bool:
    """Conservative detection of direct imperatives, not general design questions."""
    text = question.strip()
    return any(word in text for word in _TARGET_WORDS) and any(word in text for word in _ACTION_WORDS) and not is_pc_risk_question(text)


def requested_risk_count(question: str) -> int:
    for pattern in (
        r"(?:リスク|危険|懸念|問題点)[^\n。]{0,24}?(\d)\s*(?:つ|個|点)",
        r"(\d)\s*(?:つ|個|点)\s*の\s*(?:リスク|危険|懸念|問題点)",
    ):
        match = re.search(pattern, question)
        if match:
            n = int(match.group(1))
            if 1 <= n <= 5:
                return n
    return 3


def _risk_sections(answer: str) -> list[str]:
    # Examples: **リスク1: ...**, リスク 2：..., 3. ...
    header = re.compile(r"(?m)^\s*(?:\*\*)?\s*(?:リスク\s*)?([1-5])\s*[:：.．、)）]\s*")
    matches = list(header.finditer(answer))
    return [answer[m.start():matches[i + 1].start() if i + 1 < len(matches) else len(answer)]
            for i, m in enumerate(matches)]


def _execution_claims(answer: str) -> bool:
    for line in answer.splitlines():
        line = line.strip().replace("**", "")
        # A sentence about an action not being possible is not an execution claim.
        if any(neg in line for neg in ("実行しません", "実行できません", "実行していません", "行いません", "未実行", "実行する前", "実行することは")):
            continue
        if re.search(r"(?:操作|追加|削除|上書き|送信|インストール|変更|起動|購入|注文).{0,26}?(?:実行する|実行します|実行しました|完了しました)", line):
            return True
        if re.search(r"(?:ファイル|フォルダ|メール|アプリ|PC).{0,25}?(?:削除|送信|変更|起動|上書き)(?:しました|します)", line):
            return True
    return False


def review_pc_risk_answer(question: str, answer: str) -> list[str]:
    """Return user-visible problems; [] means a *heuristic* structural pass."""
    issues: list[str] = []
    expected = requested_risk_count(question)
    sections = _risk_sections(answer)
    if len(sections) != expected:
        issues.append(f"リスク項目数が指定の{expected}件と一致しない")
    for i, part in enumerate(sections):
        missing = [word for word in ("影響", "対策", "確認") if word not in part]
        if missing:
            issues.append(f"リスク{i+1}の要素不足: {', '.join(missing)}")
        if not any(word in part for word in _SPECIFIC_CONTROLS):
            issues.append(f"リスク{i+1}に具体的な技術的・運用的対策がない")
    if any(answer.count(phrase) >= 2 for phrase in (
        "ユーザーの許可を得ない限り", "ユーザーの許可が必要", "許可を得た後", "ユーザーの許可を得て"
    )):
        issues.append("許可に関する一般論が繰り返されている")
    if _execution_claims(answer):
        issues.append("権限のないPC操作の実行を宣言している")
    if not sections:
        issues.append("リスク別の見出しが見つからない")
    return issues


def claims_pc_action_completed(answer: str) -> bool:
    """Conservative non-risk screening for purported completed PC actions."""
    for line in answer.splitlines():
        if any(neg in line for neg in ("実行していません", "操作していません", "削除していません", "未実行", "できません")):
            continue
        if re.search(r"(?:PC|ファイル|フォルダ|アプリ|メール|操作|注文|購入).{0,35}?(?:実行|削除|送信|変更|上書き|起動|注文|購入)(?:しました|完了しました)", line):
            return True
    return False


def no_pc_action_reply() -> str:
    return (
        "【操作状態：未実行】\n"
        "このバージョンのトメリスにはPCを操作する機能・権限がありません。"
        "ファイル変更、削除、アプリ起動、外部送信などの操作は実行していません。\n"
        "操作内容の検討や、安全な手動手順の説明なら支援できます。"
    )


_FALLBACK_RISKS = (
    (
        "ファイルの誤削除・上書き",
        "重要な資料や設定が失われ、作業の継続が難しくなる。",
        "初期段階は読み取り専用にし、変更機能を追加する際は対象ファイルのバックアップ、差分表示、復元手順を必須にする。",
        "対象パス、変更前後の差分、バックアップの保存場所と復元方法を確認する。",
    ),
    (
        "個人情報・機密情報の漏えい",
        "不要なファイルを読み取ったり、情報を外部に送ったりするおそれがある。",
        "アクセス先を許可リストで限定し、最小権限を適用する。外部送信は初期設定で禁止し、送信先と内容を個別確認する。",
        "読み取り可能なフォルダの範囲、送信先、送信対象の情報を確認する。",
    ),
    (
        "指示の誤解による意図しない操作",
        "「整理して」を大量削除と誤解するなど、依頼と異なる変更が起こり得る。",
        "実行前に操作対象と予定作業のプレビューを表示し、変更・削除は1件ずつ承認する。操作ログを残す。",
        "提案された操作が依頼内容と一致するか、取り消し・復元が可能かを確認する。",
    ),
    (
        "不正な指示や外部データの混入",
        "読み込んだ文書中の命令を誤って実行指示と解釈するおそれがある。",
        "外部テキストは参考データとして扱い、OS操作の権限と分離する。実行範囲を許可リストで制限する。",
        "操作が現在のユーザーの明示的な依頼に由来するか、承認済み範囲内か確認する。",
    ),
    (
        "障害発生時の復旧不能",
        "途中で処理が停止し、一部だけ変更されてファイル状態が不整合になるおそれがある。",
        "変更前バックアップと操作ログを用意し、段階実行・復元方法を検証する。",
        "中断時にどこまで変更されたか確認できるか、バックアップから復元できるかを確認する。",
    ),
)


def pc_risk_fallback(question: str) -> str:
    """Reliable baseline if the small model twice fails structural safety checks."""
    n = requested_risk_count(question)
    parts = ["【安全基準に基づく回答（モデルの出力を検証し、定型回答に切り替えました）】"]
    for i, (title, impact, mitigation, check) in enumerate(_FALLBACK_RISKS[:n], 1):
        parts.append(f"**リスク{i}: {title}**\n- **影響**: {impact}\n- **具体的な対策**: {mitigation}\n- **実行前の確認**: {check}")
    parts.append("**最初の一手**: 読み取り専用の情報取得機能から設計し、変更・削除・送信は実装しない。\n"
                 "**操作状態：未実行**: ここでは設計上の提案のみを行っており、PC操作は実行していません。")
    return "\n\n".join(parts)
