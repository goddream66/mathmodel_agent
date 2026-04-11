from __future__ import annotations

from typing import Protocol

from ..state import TaskState
from ..tools import ToolRegistry


class Skill(Protocol):
    name: str

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState: ...

