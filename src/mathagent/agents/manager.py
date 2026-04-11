from __future__ import annotations

from dataclasses import dataclass

from ..memory import MemoryStore
from ..state import TaskState
from ..tools import ToolRegistry
from ..llm.config import load_llm_config
from .specialists import CodingAgent, ModelingAgent, WritingAgent


@dataclass
class ManagerAgent:
    name: str = "manager"
    modeling: ModelingAgent = ModelingAgent()
    coding: CodingAgent = CodingAgent()
    writing: WritingAgent = WritingAgent()

    def run(self, problem_text: str, tools: ToolRegistry, memory: MemoryStore) -> TaskState:
        state = TaskState(problem_text=problem_text, stage="intake")
        memory.set_shared("run_status", "started")
        memory.append_event("shared", self.name, "start", {"stage": state.stage})

        for agent_name in ["MANAGER", "MODELING", "CODING", "WRITING"]:
            cfg = load_llm_config(agent_name)
            if cfg is None:
                continue
            memory.set_agent_json(
                agent_name.lower(),
                "llm_config",
                {
                    "provider": cfg.provider,
                    "base_url": cfg.base_url,
                    "model": cfg.model,
                },
            )

        state = self.modeling.run(state, tools, memory)
        state = self.coding.run(state, tools, memory)
        state = self.writing.run(state, tools, memory)

        memory.set_shared("run_status", "finished")
        memory.append_event("shared", self.name, "finish", {"stage": state.stage})
        return state
