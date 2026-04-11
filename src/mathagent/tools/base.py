from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class Tool(Protocol):
    name: str
    description: str

    def run(self, input: Any) -> Any: ...


@dataclass
class ToolRegistry:
    _tools: dict[str, Tool]

    @classmethod
    def empty(cls) -> "ToolRegistry":
        return cls(_tools={})

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def list(self) -> list[Tool]:
        return list(self._tools.values())

