from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any

from .types import Message


@dataclass(frozen=True)
class DashScopeClient:
    api_key: str
    model: str
    base_url: str = "https://dashscope.aliyuncs.com"
    timeout_s: float = 120.0

    def chat(self, messages: list[Message], *, temperature: float = 0.2) -> str:
        url = self.base_url.rstrip("/") + "/api/v1/services/aigc/text-generation/generation"
        payload = {
            "model": self.model,
            "input": {"messages": [{"role": m.role, "content": m.content} for m in messages]},
            "parameters": {"temperature": temperature},
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

        output = data.get("output")
        if isinstance(output, dict):
            if isinstance(output.get("text"), str) and output.get("text"):
                return output["text"]
            choices = output.get("choices")
            if isinstance(choices, list) and choices:
                c0 = choices[0]
                if isinstance(c0, dict):
                    msg = c0.get("message")
                    if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                        return msg["content"]

        raise RuntimeError(f"LLM 返回结构不符合预期：{data}")

