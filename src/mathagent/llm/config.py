from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .factory import LLMConfig


def _default_config_path() -> Path:
    configured = os.getenv("MATHAGENT_LLM_CONFIG", "").strip()
    if configured:
        return Path(configured)
    return Path("config/llm.json")


def _load_file_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"LLM config file must be a JSON object: {config_path}")
    return data


def _normalize_section_name(prefix: str) -> str:
    return prefix.upper().rstrip("_")


def _coerce_options(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def load_llm_config(prefix: str, *, config_path: str | Path | None = None) -> LLMConfig | None:
    section_name = _normalize_section_name(prefix)
    path = Path(config_path) if config_path is not None else _default_config_path()
    file_config = _load_file_config(path)

    section = file_config.get(section_name)
    if section is None:
        section = file_config.get(section_name.lower())
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise ValueError(f"LLM config section must be an object: {section_name}")

    p = section_name + "_"
    api_key = str(section.get("api_key") or os.getenv(p + "API_KEY", "")).strip()
    if not api_key:
        return None

    provider = str(section.get("provider") or os.getenv(p + "PROVIDER", "openai")).strip()
    base_url = str(section.get("base_url") or os.getenv(p + "BASE_URL", "https://api.openai.com")).strip()
    model = str(section.get("model") or os.getenv(p + "MODEL", "gpt-4o-mini")).strip()
    options = _coerce_options(section.get("options"))
    return LLMConfig(
        provider=provider,
        base_url=base_url,
        api_key=api_key,
        model=model,
        options=options,
    )
