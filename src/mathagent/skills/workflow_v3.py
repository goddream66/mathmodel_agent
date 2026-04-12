from __future__ import annotations

from dataclasses import dataclass

from ..state import TaskState
from ..tools import ToolRegistry


def _render_bullets(items: list[str], *, empty_text: str = "No details yet") -> list[str]:
    if not items:
        return [f"- {empty_text}"]
    return [f"- {item}" for item in items]


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
                questions.append(f"{subproblem.title}: what is the exact target output or optimization objective?")
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
        lines: list[str] = [
            "# 摘要",
            "This fallback report summarizes the current modeling plan, structured solver outputs, and review findings. It explicitly marks missing evidence instead of fabricating results.",
            "",
            "# 问题重述",
            state.problem_text.strip(),
            "",
            "# 子问题分析与方法选择",
        ]

        for subproblem in state.subproblems:
            analysis = subproblem.analysis
            lines.extend(
                [
                    f"## {subproblem.title}",
                    subproblem.text.strip() or "No additional subproblem text was provided.",
                    "",
                    "### Objective",
                    analysis.objective or "Needs clarification",
                    "",
                    "### Candidate Models",
                    *_render_bullets(analysis.candidate_models, empty_text="No candidate models yet"),
                    "",
                    "### Chosen Method",
                    analysis.chosen_method or "Needs clarification",
                    "",
                    "### Key Variables",
                    *_render_bullets(analysis.key_variables, empty_text="No key variables yet"),
                    "",
                    "### Constraints",
                    *_render_bullets(analysis.constraints, empty_text="No explicit constraints yet"),
                    "",
                    "### Assumptions",
                    *_render_bullets(analysis.assumptions, empty_text="No explicit assumptions yet"),
                    "",
                    "### Solution Plan",
                    *_render_bullets(analysis.solution_plan, empty_text="No solution plan yet"),
                    "",
                    "### Required Data",
                    *_render_bullets(analysis.needed_data, empty_text="No required data listed"),
                    "",
                    "### Evaluation",
                    *_render_bullets(analysis.evaluation, empty_text="No evaluation metrics listed"),
                    "",
                ]
            )

        lines.extend(
            [
                "# 模型假设与符号说明",
                *_render_bullets(state.model.assumptions, empty_text="No global assumptions yet"),
                "",
                "## 建模主线",
                *_render_bullets(state.model.formulation_outline, empty_text="No global formulation outline yet"),
                "",
                "# 求解与实验",
            ]
        )

        if state.solver_runs:
            for index, solver_run in enumerate(state.solver_runs, start=1):
                lines.extend(
                    [
                        f"## Solver Run {index}: {solver_run.subproblem_title}",
                        f"- run_success: {solver_run.success}",
                        f"- schema_valid: {solver_run.schema_valid}",
                        f"- summary: {solver_run.summary}",
                        "",
                    ]
                )
                structured = solver_run.structured_result
                if structured:
                    lines.extend(
                        [
                            "### Structured Result",
                            f"- status: {structured.get('status', 'unknown')}",
                            f"- method: {structured.get('method', 'unknown')}",
                            f"- result_summary: {structured.get('result_summary', 'n/a')}",
                            "",
                        ]
                    )
                    numeric_results = dict(structured.get("numeric_results", {}))
                    if numeric_results:
                        lines.append("### Numeric Results")
                        for key, value in numeric_results.items():
                            lines.append(f"- {key}: {value}")
                        lines.append("")
                    evidence = [str(item) for item in structured.get("evidence", [])]
                    if evidence:
                        lines.extend(["### Evidence", *_render_bullets(evidence), ""])
                lines.extend(
                    [
                        "### Stdout",
                        "```text",
                        solver_run.stdout.strip() or "(empty)",
                        "```",
                        "",
                    ]
                )
                if solver_run.stderr.strip():
                    lines.extend(
                        [
                            "### Stderr",
                            "```text",
                            solver_run.stderr.strip(),
                            "```",
                            "",
                        ]
                    )
                if solver_run.artifacts:
                    lines.extend(["### Generated Artifacts", *_render_bullets(solver_run.artifacts), ""])
        else:
            lines.extend(["No solver runs are available yet.", ""])

        lines.extend(
            [
                "# 结果与分析",
                state.results.get(
                    "solver_summary",
                    "No stable quantitative result has been produced yet. Add data or improve the solver stage before final submission.",
                ),
                "",
            ]
        )

        structured_results = state.results.get("structured_solver_results", [])
        if structured_results:
            lines.append("## Structured Solver Results")
            for item in structured_results:
                if not isinstance(item, dict):
                    continue
                lines.append(f"### {item.get('subproblem_title', 'subproblem')}")
                lines.append(f"- status: {item.get('status', 'unknown')}")
                lines.append(f"- summary: {item.get('result_summary', 'n/a')}")
                for key, value in dict(item.get("numeric_results", {})).items():
                    lines.append(f"- {key}: {value}")
                evidence = [str(x) for x in item.get("evidence", [])]
                if evidence:
                    lines.extend(_render_bullets(evidence))
                lines.append("")

        findings = state.results.get("review_findings", [])
        if findings:
            lines.append("# 审稿提示")
            for finding in findings:
                lines.append(
                    f"- [{str(finding.get('severity', 'info')).upper()}] {finding.get('message', '')}"
                )
                suggestion = str(finding.get("suggestion", "")).strip()
                if suggestion:
                    lines.append(f"  Suggestion: {suggestion}")
            lines.append("")

        lines.extend(
            [
                "# 结论与后续工作",
                "The current draft already links the problem decomposition, structured solver results, and review findings. Before submission, replace baseline template results with domain-specific computations where accuracy matters.",
            ]
        )

        state.report_md = "\n".join(lines)
        state.stage = "review"
        return state
