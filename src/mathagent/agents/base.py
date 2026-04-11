from __future__ import annotations

from typing import Protocol

from ..memory import MemoryStore
from ..state import TaskState
from ..tools import ToolRegistry


class Agent(Protocol):
    name: str

    def run(self, state: TaskState, tools: ToolRegistry, memory: MemoryStore) -> TaskState: ...

