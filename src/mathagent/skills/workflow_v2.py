from __future__ import annotations

from dataclasses import dataclass

from ..state import TaskState
from ..tools import ToolRegistry


def _render_bullets(items: list[str], *, empty_text: str = "暂无") -> list[str]:
    if not items:
        return [f"- {empty_text}"]
    return [f"- {item}" for item in items]


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
                questions.append(f"{subproblem.title} 需要哪些可获得的数据或参数？")
            if not analysis.constraints:
                questions.append(f"{subproblem.title} 的硬约束和软约束分别是什么？")
            if analysis.objective is None:
                questions.append(f"{subproblem.title} 的优化或预测目标是什么？")
        if not questions:
            questions.extend(
                [
                    "题目中的决策变量、状态变量和结果变量分别是什么？",
                    "是否有必须满足的边界条件、容量上限或时间约束？",
                    "哪些结论需要定量结果支撑，哪些只能先给方法说明？",
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
        checks = [
            "变量和符号是否都已定义。",
            "目标函数与约束是否可以直接转写为模型。",
            "结论是否有计算、实验或推导支撑。",
            "结果是否可复现，是否记录了关键运行信息。",
        ]
        state.results["checks"] = checks
        state.stage = "review"
        return state


@dataclass(frozen=True)
class ReportSkill:
    name: str = "report"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        lines: list[str] = [
            "# 摘要",
            "本文围绕题目要求建立结构化建模方案，当前报告会明确哪些部分已有求解证据，哪些部分仍需补充数据或实验。",
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
                    subproblem.text.strip() or "题目没有提供额外的子问题文本。",
                    "",
                    "### 目标",
                    analysis.objective or "待进一步确认",
                    "",
                    "### 候选模型",
                    *_render_bullets(analysis.candidate_models, empty_text="待补充"),
                    "",
                    "### 建议方法",
                    analysis.chosen_method or "待补充",
                    "",
                    "### 关键变量",
                    *_render_bullets(analysis.key_variables, empty_text="待补充"),
                    "",
                    "### 约束条件",
                    *_render_bullets(analysis.constraints, empty_text="待补充"),
                    "",
                    "### 假设",
                    *_render_bullets(analysis.assumptions, empty_text="待补充"),
                    "",
                    "### 求解步骤",
                    *_render_bullets(analysis.solution_plan, empty_text="待补充"),
                    "",
                    "### 需要的数据",
                    *_render_bullets(analysis.needed_data, empty_text="待补充"),
                    "",
                    "### 评价方式",
                    *_render_bullets(analysis.evaluation, empty_text="待补充"),
                    "",
                ]
            )

        lines.extend(
            [
                "# 模型假设与符号说明",
                *_render_bullets(state.model.assumptions, empty_text="待补充"),
                "",
                "## 建模主线",
                *_render_bullets(state.model.formulation_outline, empty_text="待补充"),
                "",
                "# 求解与实验",
            ]
        )

        if state.solver_runs:
            for index, solver_run in enumerate(state.solver_runs, start=1):
                lines.extend(
                    [
                        f"## 运行 {index}: {solver_run.subproblem_title}",
                        f"- 运行状态：{'成功' if solver_run.success else '失败'}",
                        f"- 运行摘要：{solver_run.summary}",
                        "",
                        "### 标准输出",
                        "```text",
                        solver_run.stdout.strip() or "(empty)",
                        "```",
                        "",
                    ]
                )
                if solver_run.stderr.strip():
                    lines.extend(
                        [
                            "### 标准错误",
                            "```text",
                            solver_run.stderr.strip(),
                            "```",
                            "",
                        ]
                    )
                if solver_run.artifacts:
                    lines.extend(["### 生成产物", *_render_bullets(solver_run.artifacts), ""])
        else:
            lines.extend(["当前还没有实际求解运行结果，建议先执行 Coding 阶段。", ""])

        lines.extend(
            [
                "# 结果与分析",
                state.results.get("solver_summary", "当前没有形成稳定的定量结果，建议补充求解器或数据后再完善本节。"),
                "",
            ]
        )

        findings = state.results.get("review_findings", [])
        if findings:
            lines.append("# 审稿提示")
            for finding in findings:
                severity = str(finding.get("severity", "info")).upper()
                message = str(finding.get("message", ""))
                suggestion = str(finding.get("suggestion", ""))
                lines.append(f"- [{severity}] {message}")
                if suggestion:
                    lines.append(f"  建议：{suggestion}")
            lines.append("")

        lines.extend(
            [
                "# 结论与后续工作",
                "当前稿件已经形成了题目拆解、模型方向、求解记录和审稿提示的闭环。正式提交前，仍应补齐数据、数值结果和对比实验。",
            ]
        )

        state.report_md = "\n".join(lines)
        state.stage = "review"
        return state
