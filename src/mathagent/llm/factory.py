from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .dashscope import DashScopeClient
from .openai_compat import OpenAICompatClient


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    base_url: str
    api_key: str
    model: str


class LLMClient(Protocol):
    def chat(self, messages, *, temperature: float = 0.2) -> str: ...


def build_llm(config: LLMConfig) -> LLMClient:
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
