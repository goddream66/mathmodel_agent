from __future__ import annotations

from dataclasses import dataclass

from .openai_compat import OpenAICompatClient


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    base_url: str
    api_key: str
    model: str


def build_llm(config: LLMConfig) -> OpenAICompatClient:
    provider = config.provider.strip().lower()
    if provider in {"openai", "deepseek", "qwen", "bytedance", "google", "openai_compat"}:
        return OpenAICompatClient(
            base_url=config.base_url,
            api_key=config.api_key,
            model=config.model,
        )
    raise ValueError(f"不支持的 provider：{config.provider}")

