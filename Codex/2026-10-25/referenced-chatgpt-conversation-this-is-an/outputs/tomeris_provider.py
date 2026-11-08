"""TOMERIS provider adapter. Current adapter: local Ollama. Claude can implement the same interface later."""
from __future__ import annotations

import json
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    pass


class OllamaProvider:
    def __init__(self, model: str = "qwen2.5:3b", base_url: str = "http://localhost:11434", timeout: int = 180):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, path: str, payload: dict | None = None, timeout: int = 8) -> dict:
        url = self.base_url + path
        if payload is None:
            req = Request(url, method="GET")
        else:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(req, timeout=timeout) as response:
                text = response.read().decode("utf-8")
            result = json.loads(text)
            if not isinstance(result, dict):
                raise ProviderError("Ollamaから想定外の応答形式が返りました。")
            return result
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise ProviderError(f"Ollama APIエラー（HTTP {exc.code}）: {detail}") from exc
        except (URLError, socket.timeout, TimeoutError, ConnectionError) as exc:
            raise ProviderError("Ollamaに接続できません。Ollamaアプリが起動しているか確認してください。") from exc
        except json.JSONDecodeError as exc:
            raise ProviderError("OllamaからJSONとして読めない応答が返りました。") from exc

    def check(self) -> tuple[bool, str]:
        try:
            result = self._request("/api/tags", timeout=5)
            names = [item.get("name", "") for item in result.get("models", [])]
            if self.model not in names and not any(n.startswith(self.model + "-") for n in names):
                return False, f"モデル {self.model} が見つかりません。検出モデル: {', '.join(names) or 'なし'}"
            return True, "Ollamaに接続でき、指定モデルも見つかりました。"
        except ProviderError as exc:
            return False, str(exc)

    def generate(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.3, "num_ctx": 8192, "num_predict": 600},
        }
        result = self._request("/api/chat", payload=payload, timeout=self.timeout)
        message = result.get("message", {})
        answer = message.get("content", "").strip() if isinstance(message, dict) else ""
        if not answer:
            raise ProviderError("AIから空の回答が返りました。")
        return answer
