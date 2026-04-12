from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .agents import ManagerAgent
from .state import TaskState
from .tools import ToolRegistry


@dataclass
class _EphemeralMemory:
    shared: dict[str, str] = field(default_factory=dict)
    agent: dict[tuple[str, str], str] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def set_shared(self, key: str, value: str) -> None:
        self.shared[key] = value

    def get_shared(self, key: str) -> str | None:
        return self.shared.get(key)

    def set_agent(self, agent: str, key: str, value: str) -> None:
        self.agent[(agent, key)] = value

    def get_agent(self, agent: str, key: str) -> str | None:
        return self.agent.get((agent, key))

    def set_shared_json(self, key: str, value: Any) -> None:
        self.set_shared(key, json.dumps(value, ensure_ascii=False))

    def set_agent_json(self, agent: str, key: str, value: Any) -> None:
        self.set_agent(agent, key, json.dumps(value, ensure_ascii=False))

    def append_event(self, scope: str, agent: str, type: str, payload: Any) -> None:
        self.events.append(
            {"scope": scope, "agent": agent, "type": type, "payload": payload}
        )


@dataclass
class Orchestrator:
    tools: ToolRegistry
    db_path: str = "data/mathagent.db"

    def run(self, problem_text: str) -> TaskState:
        memory = _EphemeralMemory()
        return ManagerAgent().run(problem_text=problem_text, tools=self.tools, memory=memory)
