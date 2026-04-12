from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from .types import Message


def _render_string(template: str, *, base_url: str, api_key: str, model: str) -> str:
    return template.format(base_url=base_url, api_key=api_key, model=model)


def _render_template(
    value: Any,
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
) -> Any:
    if isinstance(value, dict):
        return {
            str(k): _render_template(
                v,
                base_url=base_url,
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
            )
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [
            _render_template(
                item,
                base_url=base_url,
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
            )
            for item in value
        ]
    if value == "$messages":
        return messages
    if value == "$temperature":
        return temperature
    if isinstance(value, str):
        return _render_string(value, base_url=base_url, api_key=api_key, model=model)
    return value


def _extract_path(data: Any, response_path: str) -> Any:
    current = data
    for raw_part in response_path.split("."):
        part = raw_part.strip()
        if not part:
            continue
        if isinstance(current, list):
            current = current[int(part)]
            continue
        if isinstance(current, dict):
            current = current[part]
            continue
        raise KeyError(part)
    return current


@dataclass(frozen=True)
class CustomHTTPClient:
    base_url: str
    api_key: str
    model: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body_template: dict[str, Any] = field(default_factory=dict)
    response_path: str = "choices.0.message.content"
    timeout_s: float = 120.0

    def chat(self, messages: list[Message], *, temperature: float = 0.2) -> str:
        url = self.base_url.rstrip("/") + "/" + self.path.lstrip("/")
        payload_template = self.body_template or {
            "model": "{model}",
            "messages": "$messages",
            "temperature": "$temperature",
        }
        rendered_messages = [{"role": m.role, "content": m.content} for m in messages]
        payload = _render_template(
            payload_template,
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
            messages=rendered_messages,
            temperature=temperature,
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        for key, value in self.headers.items():
            headers[key] = _render_string(
                value,
                base_url=self.base_url,
                api_key=self.api_key,
                model=self.model,
            )

        req = urllib.request.Request(
            url=url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            raise RuntimeError(f"Custom HTTP LLM request failed: {e}") from e

        try:
            data: dict[str, Any] = json.loads(body)
        except Exception as e:
            raise RuntimeError("Custom HTTP LLM response is not valid JSON") from e

        try:
            content = _extract_path(data, self.response_path)
        except Exception as e:
            raise RuntimeError(
                f"Custom HTTP LLM response does not match response_path '{self.response_path}': {data}"
            ) from e

        if not isinstance(content, str):
            raise RuntimeError(
                f"Custom HTTP LLM response_path '{self.response_path}' did not resolve to text: {content}"
            )
        return content
