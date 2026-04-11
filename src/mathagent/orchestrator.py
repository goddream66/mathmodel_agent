from __future__ import annotations

from dataclasses import dataclass

from .skills import (
    ClarifySkill,
    IntakeSkill,
    ModelSkill,
    ProblemDecomposeSkill,
    ReportSkill,
    SolveSkill,
    SubProblemAnalyzeSkill,
    ValidateSkill,
)
from .state import TaskState
from .tools import ToolRegistry


@dataclass
class Orchestrator:
    tools: ToolRegistry

    def run(self, problem_text: str) -> TaskState:
        state = TaskState(problem_text=problem_text, stage="intake")
        skills = [
            IntakeSkill(),
            ProblemDecomposeSkill(),
            SubProblemAnalyzeSkill(),
            ClarifySkill(),
            ModelSkill(),
            SolveSkill(),
            ValidateSkill(),
            ReportSkill(),
        ]
        for skill in skills:
            state = skill.run(state, self.tools)
        return state
