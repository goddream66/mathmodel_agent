from __future__ import annotations

import json
import re
from typing import Any


def extract_first_json(text: str) -> Any:
    s = text.strip()
    if not s:
        raise ValueError("empty")

    if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
        return json.loads(s)

    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s, flags=re.IGNORECASE)
    if fence:
        return json.loads(fence.group(1))

    first_obj = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", s)
    if first_obj:
        return json.loads(first_obj.group(1))

    raise ValueError("no json found")

