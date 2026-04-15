from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any

from .types import Message


def _build_chat_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    if normalized.endswith("/v1"):
        return normalized + "/chat/completions"
    return normalized + "/v1/chat/completions"


@dataclass(frozen=True)
class OpenAICompatClient:
    base_url: str
    api_key: str
    model: str
    timeout_s: float = 120.0

    def chat(self, messages: list[Message], *, temperature: float = 0.2) -> str:
        url = _build_chat_url(self.base_url)
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }

        req = urllib.request.Request(
            url=url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            raise RuntimeError(f"LLM 请求失败：{e}") from e

        try:
            data: dict[str, Any] = json.loads(body)
        except Exception as e:
            raise RuntimeError("LLM 返回不是合法 JSON") from e

        try:
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"LLM 返回结构不符合预期：{data}") from e
