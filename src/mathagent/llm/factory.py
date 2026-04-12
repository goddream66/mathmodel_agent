from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from .custom_http import CustomHTTPClient
from .dashscope import DashScopeClient
from .openai_compat import OpenAICompatClient


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    base_url: str
    api_key: str
    model: str
    options: dict[str, Any] = field(default_factory=dict)


class LLMClient(Protocol):
    def chat(self, messages, *, temperature: float = 0.2) -> str: ...


Builder = Callable[[LLMConfig], LLMClient]


def _build_openai_compat(config: LLMConfig) -> LLMClient:
    return OpenAICompatClient(
        base_url=config.base_url,
        api_key=config.api_key,
        model=config.model,
    )


def _build_dashscope(config: LLMConfig) -> LLMClient:
    return DashScopeClient(
        api_key=config.api_key,
        model=config.model,
        base_url=config.base_url or "https://dashscope.aliyuncs.com",
    )


def _build_custom_http(config: LLMConfig) -> LLMClient:
    return CustomHTTPClient(
        base_url=config.base_url,
        api_key=config.api_key,
        model=config.model,
        path=str(config.options.get("path") or "/v1/chat/completions"),
        headers=dict(config.options.get("headers") or {}),
        body_template=dict(config.options.get("body") or {}),
        response_path=str(config.options.get("response_path") or "choices.0.message.content"),
        timeout_s=float(config.options.get("timeout_s") or 120.0),
    )


PROVIDER_BUILDERS: dict[str, Builder] = {
    "openai": _build_openai_compat,
    "deepseek": _build_openai_compat,
    "qwen": _build_openai_compat,
    "bytedance": _build_openai_compat,
    "google": _build_openai_compat,
    "openai_compat": _build_openai_compat,
    "aliyun": _build_dashscope,
    "dashscope": _build_dashscope,
    "alibaba": _build_dashscope,
    "custom_http": _build_custom_http,
}


def register_provider(provider: str, builder: Builder) -> None:
    PROVIDER_BUILDERS[provider.strip().lower()] = builder


def build_llm(config: LLMConfig) -> LLMClient:
    provider = config.provider.strip().lower()
    builder = PROVIDER_BUILDERS.get(provider)
    if builder is None:
        supported = ", ".join(sorted(PROVIDER_BUILDERS))
        raise ValueError(f"Unsupported provider: {config.provider}. Supported providers: {supported}")
    return builder(config)


def _legacy_build_llm(config: LLMConfig) -> LLMClient:
    provider = config.provider.strip().lower()
    if provider in {"openai", "deepseek", "qwen", "bytedance", "google", "openai_compat"}:
        return OpenAICompatClient(
            base_url=config.base_url,
            api_key=config.api_key,
            model=config.model,
        )
    if provider in {"aliyun", "dashscope", "alibaba"}:
        return DashScopeClient(
            api_key=config.api_key,
            model=config.model,
            base_url=config.base_url or "https://dashscope.aliyuncs.com",
        )
    raise ValueError(f"不支持的 provider：{config.provider}")
