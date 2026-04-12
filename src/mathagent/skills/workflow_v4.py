from __future__ import annotations

from dataclasses import dataclass

from ..reporting import render_fallback_report
from ..state import TaskState
from ..tools import ToolRegistry


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        clean = item.strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        output.append(clean)
    return output


@dataclass(frozen=True)
class IntakeSkill:
    name: str = "intake"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        state.stage = "clarify"
        return state


@dataclass(frozen=True)
class ClarifySkill:
    name: str = "clarify"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        questions: list[str] = []
        for subproblem in state.subproblems:
            analysis = subproblem.analysis
            if not analysis.needed_data:
                questions.append(f"{subproblem.title}: what data or parameters are still missing?")
            if not analysis.constraints:
                questions.append(f"{subproblem.title}: what are the hard and soft constraints?")
            if analysis.objective is None:
                questions.append(
                    f"{subproblem.title}: what is the exact target output or optimization objective?"
                )
        if not questions:
            questions.extend(
                [
                    "Which variables are the decision variables, state variables, and outputs?",
                    "Which constraints must always hold?",
                    "Which claims require quantitative evidence before they can appear in the final paper?",
                ]
            )
        state.clarifications = questions[:6]
        state.stage = "model"
        return state


@dataclass(frozen=True)
class ModelSkill:
    name: str = "model"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        method_candidates: list[str] = []
        assumptions: list[str] = []
        constraints: list[str] = []
        formulation_outline: list[str] = []
        evidence_gaps: list[str] = []

        for subproblem in state.subproblems:
            analysis = subproblem.analysis
            method_candidates.extend(analysis.candidate_models)
            assumptions.extend(analysis.assumptions)
            constraints.extend(analysis.constraints)
            formulation_outline.extend(analysis.formulation_steps)
            evidence_gaps.extend(analysis.needed_data)

        state.model.method_candidates = _unique(method_candidates)[:8]
        state.model.assumptions = _unique(assumptions)[:8]
        state.model.constraints = _unique(constraints)[:8]
        state.model.formulation_outline = _unique(formulation_outline)[:10]
        state.model.evidence_gaps = _unique(evidence_gaps)[:8]
        state.model.objective = state.subproblems[0].analysis.objective if state.subproblems else None
        if state.subproblems and state.subproblems[0].analysis.chosen_method:
            state.model.chosen_method = state.subproblems[0].analysis.chosen_method
        state.stage = "solve"
        return state


@dataclass(frozen=True)
class SolveSkill:
    name: str = "solve"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        if "status" not in state.results:
            state.results["status"] = "pending_solver"
        state.stage = "validate"
        return state


@dataclass(frozen=True)
class ValidateSkill:
    name: str = "validate"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        state.results["checks"] = [
            "Are all variables and symbols defined consistently?",
            "Can the objective and constraints be written as a formal model?",
            "Does each conclusion have computational or analytical evidence?",
            "Can the result be reproduced from the recorded artifacts and solver outputs?",
        ]
        state.stage = "review"
        return state


@dataclass(frozen=True)
class ReportSkill:
    name: str = "report"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        state.report_md = render_fallback_report(state)
        state.stage = "review"
        return state
