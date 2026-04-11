from __future__ import annotations

import os

from .factory import LLMConfig


def load_llm_config(prefix: str) -> LLMConfig | None:
    p = prefix.upper().rstrip("_") + "_"
    api_key = os.getenv(p + "API_KEY", "").strip()
    if not api_key:
        return None

    provider = os.getenv(p + "PROVIDER", "openai").strip()
    base_url = os.getenv(p + "BASE_URL", "https://api.openai.com").strip()
    model = os.getenv(p + "MODEL", "gpt-4o-mini").strip()
    return LLMConfig(provider=provider, base_url=base_url, api_key=api_key, model=model)

