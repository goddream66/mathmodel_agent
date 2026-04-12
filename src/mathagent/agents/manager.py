from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ..llm.config import load_llm_config
from ..memory import MemoryStore
from ..state import TaskState
from ..tools import ToolRegistry
from .base import Agent
from .specialists_v3 import CodingAgent, ModelingAgent, ReviewAgent, WritingAgent


@dataclass
class ManagerAgent:
    name: str = "manager"
    modeling: ModelingAgent = field(default_factory=ModelingAgent)
    coding: CodingAgent = field(default_factory=CodingAgent)
    review: ReviewAgent = field(default_factory=ReviewAgent)
    writing: WritingAgent = field(default_factory=WritingAgent)

    def _agents(self) -> dict[str, Agent]:
        return {
            self.modeling.name: self.modeling,
            self.coding.name: self.coding,
            self.review.name: self.review,
            self.writing.name: self.writing,
        }

    def _configured_agent_names(self) -> Iterable[str]:
        yield "MANAGER"
        for agent in self._agents().values():
            yield agent.name.upper()

    def _record_config(self, memory: MemoryStore) -> None:
        for agent_name in self._configured_agent_names():
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

    def _snapshot_state(self, state: TaskState, memory: MemoryStore) -> None:
        memory.set_shared("stage", state.stage)
        memory.set_shared("problem_text", state.problem_text)
        memory.set_shared_json(
            "state_snapshot",
            {
                "stage": state.stage,
                "clarifications": state.clarifications,
                "input_data": state.input_data,
                "results": state.results,
                "model": {
                    "objective": state.model.objective,
                    "constraints": state.model.constraints,
                    "assumptions": state.model.assumptions,
                    "method_candidates": state.model.method_candidates,
                    "chosen_method": state.model.chosen_method,
                    "formulation_outline": state.model.formulation_outline,
                    "evidence_gaps": state.model.evidence_gaps,
                },
                "solver_runs": [
                    {
                        "subproblem_title": run.subproblem_title,
                        "success": run.success,
                        "summary": run.summary,
                        "stdout": run.stdout,
                        "stderr": run.stderr,
                        "artifacts": run.artifacts,
                        "structured_result": run.structured_result,
                        "schema_valid": run.schema_valid,
                    }
                    for run in state.solver_runs
                ],
                "subproblems": [
                    {
                        "title": sp.title,
                        "text": sp.text,
                        "analysis": {
                            "task_types": sp.analysis.task_types,
                            "candidate_models": sp.analysis.candidate_models,
                            "solution_plan": sp.analysis.solution_plan,
                            "key_variables": sp.analysis.key_variables,
                            "needed_data": sp.analysis.needed_data,
                            "evaluation": sp.analysis.evaluation,
                            "notes": sp.analysis.notes,
                            "objective": sp.analysis.objective,
                            "constraints": sp.analysis.constraints,
                            "assumptions": sp.analysis.assumptions,
                            "deliverables": sp.analysis.deliverables,
                            "formulation_steps": sp.analysis.formulation_steps,
                            "chosen_method": sp.analysis.chosen_method,
                            "confidence": sp.analysis.confidence,
                        },
                    }
                    for sp in state.subproblems
                ],
            },
        )
        if state.report_md is not None:
            memory.set_shared("report_md", state.report_md)

    def _next_agent_name(self, state: TaskState) -> str | None:
        if not state.subproblems:
            return self.modeling.name
        if state.results.get("status") is None:
            return self.coding.name
        if not state.results.get("reviewed_solution"):
            return self.review.name
        if not state.report_md:
            return self.writing.name
        if not state.results.get("final_review_done"):
            return self.review.name
        return None

    def run(
        self,
        problem_text: str,
        tools: ToolRegistry,
        memory: MemoryStore,
        *,
        input_data: dict | None = None,
    ) -> TaskState:
        state = TaskState(problem_text=problem_text, stage="intake", input_data=input_data or {})
        memory.set_shared("run_status", "started")
        memory.append_event("shared", self.name, "start", {"stage": state.stage})
        self._record_config(memory)

        agents = self._agents()
        while True:
            next_agent_name = self._next_agent_name(state)
            if next_agent_name is None:
                break

            memory.append_event("shared", self.name, "dispatch", {"agent": next_agent_name})
            state = agents[next_agent_name].run(state, tools, memory)
            self._snapshot_state(state, memory)

        state.stage = "done"
        self._snapshot_state(state, memory)
        memory.set_shared("run_status", "finished")
        memory.append_event("shared", self.name, "finish", {"stage": state.stage})
        return state
