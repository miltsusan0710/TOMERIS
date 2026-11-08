"""TOMERIS common memory engine v0.4.1 (stdlib only).

Memory is provider-independent: any future LLM adapter can consume build_context().
Existing v0.3.x tomeris_memory.json files are migrated additively only after a successful backup.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import json
import re
import shutil

ENGINE_VERSION = "0.4.1"
SCHEMA_VERSION = 3


def timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _query_terms(text: str) -> set[str]:
    """Lightweight bilingual search terms without third-party tokenizers.

    Latin/digit terms are word-based; Japanese/Chinese/Kana text uses bigrams.
    This is heuristic search, not semantic/vector search.
    """
    text = text.lower()
    terms = set(re.findall(r"[a-z0-9_+-]{2,}", text))
    cjk_runs = re.findall(r"[\u3040-\u30ff\u3400-\u9fff]+", text)
    stop = {"こと", "もの", "ため", "です", "ます", "する", "した", "して", "いる", "ある", "これ", "それ", "そして", "から", "まで", "について", "ください", "お願い", "私の", "あなた", "トメリス"}
    for run in cjk_runs:
        if len(run) == 1:
            terms.add(run)
        else:
            for i in range(len(run) - 1):
                gram = run[i:i + 2]
                if gram not in stop:
                    terms.add(gram)
    return terms


def _relevance(query: str, text: str) -> int:
    q = query.strip().lower()
    target = text.lower()
    if not q or not target:
        return 0
    score = 8 if q in target else 0
    terms = _query_terms(q)
    t_terms = _query_terms(target)
    score += len(terms & t_terms)
    return score


class MemoryStore:
    """Local, JSON-backed memory storage, independent from any AI provider."""

    def __init__(self, memory_file: Path, knowledge_dir: Path):
        self.path = Path(memory_file)
        self.knowledge_dir = Path(knowledge_dir)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.last_backup: Path | None = None
        self.data = self._load_and_normalize()

    def _new_data(self) -> dict[str, Any]:
        return {
            "version": 3,
            "created_at": timestamp(),
            "conversations": [],
            "growth_log": [],
            "memories": [],
            "decisions": [],
            "metadata": {"memory_engine": ENGINE_VERSION, "next_memory_id": 1},
        }

    def _backup_once(self) -> None:
        if not self.path.exists():
            return
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = self.path.with_name(f"{self.path.stem}_backup_{stamp}{self.path.suffix}")
        counter = 1
        while backup.exists():
            backup = self.path.with_name(
                f"{self.path.stem}_backup_{stamp}_{counter}{self.path.suffix}"
            )
            counter += 1
        try:
            shutil.copy2(self.path, backup)
            self.last_backup = backup
        except OSError:
            self.last_backup = None

    def _load_and_normalize(self) -> dict[str, Any]:
        if not self.path.exists():
            data = self._new_data()
            self._save_data(data)
            return data

        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError("記憶ファイルの最上位がJSONオブジェクトではありません")
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            # Preserve the damaged file; do not silently overwrite it with an empty store.
            self._backup_once()
            raise RuntimeError(
                f"記憶ファイルを読み込めませんでした: {exc}\n"
                "元ファイルを自動で上書きしていません。バックアップとJSON形式を確認してください。"
            ) from exc

        raw_version = loaded.get("version", 0)
        # Treat non-numeric/malformed version values as legacy; do not crash comparing strings to ints.
        version = raw_version if isinstance(raw_version, (int, float)) and not isinstance(raw_version, bool) else 0
        if version > SCHEMA_VERSION:
            raise RuntimeError(
                f"記憶ファイルのスキーマ版 {version} は、このエンジンが扱える版 {SCHEMA_VERSION} より新しいです。"
                "データを変更せずに停止しました。対応版のトメリスで開いてください。"
            )
        required_lists = ("conversations", "growth_log", "memories", "decisions")
        needs_backup = (
            version < SCHEMA_VERSION
            or any(not isinstance(loaded.get(key), list) for key in required_lists)
            or not isinstance(loaded.get("metadata"), dict)
        )
        if needs_backup:
            self._backup_once()
            if self.last_backup is None:
                raise RuntimeError(
                    "旧形式の記憶ファイルを移行する前のバックアップを作成できませんでした。"
                    "元ファイルを変更せず停止しました。フォルダーの書き込み権限と空き容量を確認してください。"
                )
        data = loaded
        defaults = self._new_data()
        for key, value in defaults.items():
            if key not in data:
                data[key] = value
        for key in ("conversations", "growth_log", "memories", "decisions"):
            if not isinstance(data.get(key), list):
                data[key] = []
        if not isinstance(data.get("metadata"), dict):
            data["metadata"] = {}
        data["metadata"]["memory_engine"] = ENGINE_VERSION
        existing_ids = []
        for item in data.get("memories", []):
            if isinstance(item, dict):
                match = re.fullmatch(r"M(\d+)", str(item.get("id", "")))
                if match:
                    existing_ids.append(int(match.group(1)))
        minimum_next_id = max(existing_ids, default=0) + 1
        try:
            stored_next_id = int(data["metadata"].get("next_memory_id", 1))
        except (TypeError, ValueError):
            stored_next_id = 1
        data["metadata"]["next_memory_id"] = max(minimum_next_id, stored_next_id, 1)
        data["version"] = SCHEMA_VERSION
        self._save_data(data)
        return data

    def _save_data(self, data: dict[str, Any] | None = None) -> None:
        source = data if data is not None else self.data
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = json.dumps(source, ensure_ascii=False, indent=2)
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(self.path)

    def save(self) -> None:
        self._save_data()

    def add_conversation(self, user_text: str, assistant_text: str) -> None:
        self.data["conversations"].append({
            "timestamp": timestamp(),
            "user": user_text,
            "tomeris": assistant_text,
        })
        self.save()

    def add_growth(self, category: str, text: str) -> None:
        self.data["growth_log"].append({
            "timestamp": timestamp(),
            "category": category or "その他",
            "text": text,
        })
        self.save()

    def add_memory(self, category: str, text: str, tags: str = "", importance: int = 3) -> dict[str, Any]:
        text = text.strip()
        if not text:
            raise ValueError("記憶する文章が空です")
        ids = []
        for item in self.data["memories"]:
            match = re.fullmatch(r"M(\d+)", str(item.get("id", ""))) if isinstance(item, dict) else None
            if match:
                ids.append(int(match.group(1)))
        try:
            stored_next_id = int(self.data["metadata"].get("next_memory_id", 1))
        except (TypeError, ValueError):
            stored_next_id = 1
        next_id = max(max(ids, default=0) + 1, stored_next_id, 1)
        record = {
            "id": f"M{next_id:04d}",
            "timestamp": timestamp(),
            "category": category or "その他",
            "text": text,
            "tags": [x.strip() for x in re.split(r"[,、;；]", tags) if x.strip()],
            "importance": max(1, min(5, int(importance))),
            "source": "user_explicit",
        }
        self.data["memories"].append(record)
        self.data["metadata"]["next_memory_id"] = next_id + 1
        self.save()
        return record

    def forget_memory(self, memory_id: str) -> bool:
        target = memory_id.strip().upper()
        before = len(self.data["memories"])
        self.data["memories"] = [
            item for item in self.data["memories"]
            if not (isinstance(item, dict) and str(item.get("id", "")).upper() == target)
        ]
        changed = len(self.data["memories"]) != before
        if changed:
            self.save()
        return changed

    def recent_conversations(self, limit: int = 10) -> list[dict[str, Any]]:
        return [item for item in self.data["conversations"][-limit:] if isinstance(item, dict)]

    def recent_growth(self, limit: int = 20) -> list[dict[str, Any]]:
        return [item for item in self.data["growth_log"][-limit:] if isinstance(item, dict)]

    def search_memory(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        scored = []
        for item in self.data["memories"]:
            if not isinstance(item, dict):
                continue
            haystack = " ".join([
                _safe_text(item.get("category")), _safe_text(item.get("text")),
                " ".join(str(tag) for tag in item.get("tags", [])) if isinstance(item.get("tags"), list) else "",
            ])
            score = _relevance(query, haystack)
            if score:
                try:
                    importance = max(1, min(5, int(item.get("importance", 3))))
                except (ValueError, TypeError):
                    importance = 3
                score += importance
                scored.append((score, item))
        scored.sort(key=lambda x: (x[0], _safe_text(x[1].get("timestamp"))), reverse=True)
        return [item for _, item in scored[:limit]]

    def search_growth(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        scored = []
        for item in self.data["growth_log"]:
            if not isinstance(item, dict):
                continue
            text = f"{_safe_text(item.get('category'))} {_safe_text(item.get('text'))}"
            score = _relevance(query, text)
            if score:
                scored.append((score, item))
        scored.sort(key=lambda x: (x[0], _safe_text(x[1].get("timestamp"))), reverse=True)
        return [item for _, item in scored[:limit]]

    def search_conversations(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        scored = []
        for item in self.data["conversations"]:
            if not isinstance(item, dict):
                continue
            text = f"{_safe_text(item.get('user'))} {_safe_text(item.get('tomeris'))}"
            score = _relevance(query, text)
            if score:
                scored.append((score, item))
        scored.sort(key=lambda x: (x[0], _safe_text(x[1].get("timestamp"))), reverse=True)
        return [item for _, item in scored[:limit]]

    def search_knowledge(self, query: str, limit: int = 3) -> list[dict[str, str]]:
        scored: list[tuple[int, dict[str, str]]] = []
        for file in self.knowledge_dir.rglob("*"):
            if not file.is_file() or file.suffix.lower() not in {".md", ".txt"}:
                continue
            try:
                content = file.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            score = _relevance(query, f"{file.stem} {content}")
            if score:
                scored.append((score, {"path": str(file.relative_to(self.knowledge_dir)), "content": content[:5000]}))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def build_context(self, query: str, max_recent: int = 3) -> str:
        sections: list[str] = []
        memories = self.search_memory(query, limit=5)
        if memories:
            lines = []
            for item in memories:
                tags = ", ".join(item.get("tags", [])) if isinstance(item.get("tags"), list) else ""
                lines.append(f"- [{item.get('id')}][{item.get('category')}] {item.get('text')}" + (f"（タグ: {tags}）" if tags else ""))
            sections.append("【関連する長期記憶】\n" + "\n".join(lines))

        growth = self.search_growth(query, limit=3)
        if growth:
            lines = [f"- [{x.get('category', 'その他')}] {x.get('text', '')}" for x in growth]
            sections.append("【関連する成長ログ】\n" + "\n".join(lines))

        conversations = self.search_conversations(query, limit=max_recent)
        if conversations:
            lines = []
            for item in conversations:
                u = _safe_text(item.get("user"))[-400:]
                a = _safe_text(item.get("tomeris"))[:600]
                lines.append(f"ユーザー: {u}\nトメリス: {a}")
            sections.append("【関連する過去の会話】\n" + "\n---\n".join(lines))

        knowledge = self.search_knowledge(query, limit=2)
        if knowledge:
            lines = [f"--- {x['path']} ---\n{x['content']}" for x in knowledge]
            sections.append("【関連するローカル知識資料】\n" + "\n\n".join(lines))

        if not sections:
            return "関連する長期記憶・成長ログ・過去会話・ローカル知識はまだありません。"
        return "\n\n".join(sections)

    def stats(self) -> dict[str, int]:
        return {
            "conversations": len(self.data["conversations"]),
            "growth_log": len(self.data["growth_log"]),
            "memories": len(self.data["memories"]),
            "knowledge_files": sum(1 for p in self.knowledge_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".txt"}),
        }
