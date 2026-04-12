from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


Stage = Literal[
    "intake",
    "clarify",
    "model",
    "solve",
    "validate",
    "review",
    "report",
    "done",
]


@dataclass
class ModelSpec:
    assumptions: list[str] = field(default_factory=list)
    symbols: dict[str, str] = field(default_factory=dict)
    objective: str | None = None
    constraints: list[str] = field(default_factory=list)
    method_candidates: list[str] = field(default_factory=list)
    chosen_method: str | None = None
    formulation_outline: list[str] = field(default_factory=list)
    evidence_gaps: list[str] = field(default_factory=list)


@dataclass
class ExperimentArtifact:
    name: str
    kind: Literal["table", "figure", "text", "file", "json", "code"]
    payload: Any


@dataclass
class SubProblemAnalysis:
    task_types: list[str] = field(default_factory=list)
    candidate_models: list[str] = field(default_factory=list)
    solution_plan: list[str] = field(default_factory=list)
    key_variables: list[str] = field(default_factory=list)
    needed_data: list[str] = field(default_factory=list)
    evaluation: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    objective: str | None = None
    constraints: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    deliverables: list[str] = field(default_factory=list)
    formulation_steps: list[str] = field(default_factory=list)
    chosen_method: str | None = None
    confidence: float | None = None


@dataclass
class SubProblem:
    title: str
    text: str
    analysis: SubProblemAnalysis = field(default_factory=SubProblemAnalysis)


@dataclass
class SolverRun:
    subproblem_title: str
    success: bool
    summary: str
    code: str
    stdout: str = ""
    stderr: str = ""
    artifacts: list[str] = field(default_factory=list)
    structured_result: dict[str, Any] = field(default_factory=dict)
    schema_valid: bool = False


@dataclass
class ConversationTurn:
    role: Literal["user", "assistant", "system"]
    content: str


@dataclass
class TaskState:
    problem_text: str
    stage: Stage = "intake"
    clarifications: list[str] = field(default_factory=list)
    subproblems: list[SubProblem] = field(default_factory=list)
    model: ModelSpec = field(default_factory=ModelSpec)
    input_data: dict[str, Any] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    artifacts: list[ExperimentArtifact] = field(default_factory=list)
    solver_runs: list[SolverRun] = field(default_factory=list)
    conversation: list[ConversationTurn] = field(default_factory=list)
    report_md: str | None = None
