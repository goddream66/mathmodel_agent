from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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

    @classmethod
    def with_defaults(cls, *, out_dir: str | Path = "outputs") -> "ToolRegistry":
        from .python_exec import PythonExecTool

        registry = cls.empty()
        registry.register(PythonExecTool(work_dir=Path(out_dir) / "tool_runs"))
        return registry

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def maybe_get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list(self) -> list[Tool]:
        return list(self._tools.values())
