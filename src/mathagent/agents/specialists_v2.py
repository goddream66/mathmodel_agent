from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..llm import Message, build_llm
from ..llm.config import load_llm_config
from ..llm.utils import extract_first_json
from ..memory import MemoryStore
from ..prompts import render_prompt
from ..skills import (
    ClarifySkill,
    ModelSkill,
    ProblemDecomposeSkill,
    ReportSkill,
    SolveSkill,
    SubProblemAnalyzeSkill,
    ValidateSkill,
)
from ..state import ExperimentArtifact, SolverRun, SubProblem, TaskState
from ..tools import ToolRegistry


def _subproblems_payload(state: TaskState) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for subproblem in state.subproblems:
        payload.append(
            {
                "title": subproblem.title,
                "text": subproblem.text,
                "analysis": {
                    "task_types": subproblem.analysis.task_types,
                    "candidate_models": subproblem.analysis.candidate_models,
                    "solution_plan": subproblem.analysis.solution_plan,
                    "key_variables": subproblem.analysis.key_variables,
                    "needed_data": subproblem.analysis.needed_data,
                    "evaluation": subproblem.analysis.evaluation,
                    "notes": subproblem.analysis.notes,
                    "objective": subproblem.analysis.objective,
                    "constraints": subproblem.analysis.constraints,
                    "assumptions": subproblem.analysis.assumptions,
                    "deliverables": subproblem.analysis.deliverables,
                    "formulation_steps": subproblem.analysis.formulation_steps,
                    "chosen_method": subproblem.analysis.chosen_method,
                    "confidence": subproblem.analysis.confidence,
                },
            }
        )
    return payload


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    output: list[str] = []
    for item in value:
        clean = str(item).strip()
        if clean:
            output.append(clean)
    return output


def _load_solver_artifacts(run_dir: str, artifact_names: list[str]) -> list[ExperimentArtifact]:
    base_path = Path(run_dir)
    artifacts: list[ExperimentArtifact] = []
    for artifact_name in artifact_names:
        artifact_path = base_path / artifact_name
        if not artifact_path.exists() or not artifact_path.is_file():
            continue
        suffix = artifact_path.suffix.lower()
        if suffix == ".json":
            try:
                payload = json.loads(artifact_path.read_text(encoding="utf-8"))
                kind = "json"
            except Exception:
                payload = artifact_path.read_text(encoding="utf-8", errors="replace")
                kind = "text"
        elif suffix == ".py":
            payload = artifact_path.read_text(encoding="utf-8", errors="replace")
            kind = "code"
        else:
            payload = artifact_path.read_text(encoding="utf-8", errors="replace")
            kind = "text"
        artifacts.append(ExperimentArtifact(name=artifact_name, kind=kind, payload=payload))
    return artifacts


def _build_solver_context(state: TaskState) -> dict[str, Any]:
    return {
        "problem_text": state.problem_text,
        "clarifications": state.clarifications,
        "subproblems": _subproblems_payload(state),
        "model": {
            "assumptions": state.model.assumptions,
            "constraints": state.model.constraints,
            "method_candidates": state.model.method_candidates,
            "chosen_method": state.model.chosen_method,
            "formulation_outline": state.model.formulation_outline,
            "evidence_gaps": state.model.evidence_gaps,
        },
    }


def _build_fallback_solver_code(state: TaskState) -> tuple[str, str]:
    context_json = json.dumps(_build_solver_context(state), ensure_ascii=False, indent=2)
    summary = "Used built-in fallback solver to create structured notes and extract simple numerical signals."
    code = f"""from __future__ import annotations
import json
import re
from pathlib import Path

context = {context_json}
problem_text = context["problem_text"]
numbers = [float(x) for x in re.findall(r"-?\\d+(?:\\.\\d+)?", problem_text)]
summary = {{
    "subproblem_count": len(context["subproblems"]),
    "subproblem_titles": [item["title"] for item in context["subproblems"]],
    "recommended_methods": [
        item["analysis"].get("chosen_method") or "待确认"
        for item in context["subproblems"]
    ],
    "detected_numbers": numbers[:20],
}}
Path("solver_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
lines = [
    "# Solver Notes",
    "",
    f"- subproblem_count: {{summary['subproblem_count']}}",
    f"- detected_numbers: {{summary['detected_numbers']}}",
]
for item in context["subproblems"]:
    analysis = item["analysis"]
    lines.extend(
        [
            "",
            f"## {{item['title']}}",
            f"- objective: {{analysis.get('objective') or '待确认'}}",
            f"- chosen_method: {{analysis.get('chosen_method') or '待确认'}}",
            "- constraints:",
        ]
    )
    constraints = analysis.get("constraints") or ["待补充"]
    for constraint in constraints:
        lines.append(f"  - {{constraint}}")
Path("solver_notes.md").write_text("\\n".join(lines), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))
"""
    return summary, code


def _extract_code_block(text: str) -> str:
    match = re.search(r"```python\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def _build_llm_solver(state: TaskState) -> tuple[str, str]:
    cfg = load_llm_config("CODING")
    if cfg is None:
        return _build_fallback_solver_code(state)

    llm = build_llm(cfg)
    response = llm.chat(
        [
            Message(role="system", content=render_prompt("coding_system")),
            Message(
                role="user",
                content=render_prompt(
                    "coding_user",
                    problem_text=state.problem_text,
                    context_json=json.dumps(_build_solver_context(state), ensure_ascii=False, indent=2),
                ),
            ),
        ],
        temperature=0.1,
    )
    try:
        payload = extract_first_json(response)
        if isinstance(payload, dict):
            summary = str(payload.get("summary") or "").strip() or "Generated code from CODING LLM."
            code = _extract_code_block(str(payload.get("code") or ""))
            if code:
                return summary, code
    except Exception:
        pass
    code = _extract_code_block(response)
    if code:
        return "Generated code from CODING LLM.", code
    return _build_fallback_solver_code(state)


def _required_report_sections() -> list[str]:
    return [
        "# 摘要",
        "# 问题重述",
        "# 子问题分析与方法选择",
        "# 模型假设与符号说明",
        "# 求解与实验",
        "# 结果与分析",
        "# 结论与后续工作",
    ]


def _append_finding(findings: list[dict[str, str]], *, severity: str, area: str, message: str, suggestion: str) -> None:
    findings.append(
        {
            "severity": severity,
            "area": area,
            "message": message,
            "suggestion": suggestion,
        }
    )


@dataclass(frozen=True)
class ModelingAgent:
    name: str = "modeling"

    def run(self, state: TaskState, tools: ToolRegistry, memory: MemoryStore) -> TaskState:
        state = ProblemDecomposeSkill().run(state, tools)
        state = SubProblemAnalyzeSkill().run(state, tools)
        state = ClarifySkill().run(state, tools)
        state = ModelSkill().run(state, tools)

        cfg = load_llm_config("MODELING")
        if cfg is not None:
            llm = build_llm(cfg)
            try:
                payload = extract_first_json(
                    llm.chat(
                        [
                            Message(role="system", content=render_prompt("modeling_system")),
                            Message(
                                role="user",
                                content=render_prompt(
                                    "modeling_user",
                                    problem_text=state.problem_text,
                                ),
                            ),
                        ],
                        temperature=0.2,
                    )
                )
                if isinstance(payload, list) and payload:
                    state.subproblems = []
                    for index, item in enumerate(payload, start=1):
                        if not isinstance(item, dict):
                            continue
                        subproblem = SubProblem(
                            title=str(item.get("title") or f"子问题{index}").strip(),
                            text=str(item.get("text") or "").strip(),
                        )
                        analysis = subproblem.analysis
                        analysis.task_types = _string_list(item.get("task_types"))
                        analysis.candidate_models = _string_list(item.get("candidate_models"))
                        analysis.solution_plan = _string_list(item.get("solution_plan"))
                        analysis.key_variables = _string_list(item.get("key_variables"))
                        analysis.needed_data = _string_list(item.get("needed_data"))
                        analysis.evaluation = _string_list(item.get("evaluation"))
                        analysis.notes = _string_list(item.get("notes"))
                        analysis.objective = str(item.get("objective") or "").strip() or None
                        analysis.constraints = _string_list(item.get("constraints"))
                        analysis.assumptions = _string_list(item.get("assumptions"))
                        analysis.deliverables = _string_list(item.get("deliverables"))
                        analysis.formulation_steps = _string_list(item.get("formulation_steps"))
                        analysis.chosen_method = str(item.get("chosen_method") or "").strip() or None
                        if isinstance(item.get("confidence"), (float, int)):
                            analysis.confidence = float(item["confidence"])
                        state.subproblems.append(subproblem)
                    state = ClarifySkill().run(state, tools)
                    state = ModelSkill().run(state, tools)
            except Exception as exc:
                memory.set_agent_json(self.name, "llm_error", {"error": str(exc)})
                memory.append_event("agent", self.name, "llm_error", {"error": str(exc)})

        memory.set_shared("problem_text", state.problem_text)
        memory.set_shared_json("subproblems", _subproblems_payload(state))
        memory.set_agent_json(self.name, "clarifications", state.clarifications)
        memory.set_agent_json(
            self.name,
            "model_overview",
            {
                "chosen_method": state.model.chosen_method,
                "method_candidates": state.model.method_candidates,
                "assumptions": state.model.assumptions,
                "constraints": state.model.constraints,
                "formulation_outline": state.model.formulation_outline,
            },
        )
        memory.append_event("agent", self.name, "done", {"stage": state.stage})
        return state


@dataclass(frozen=True)
class CodingAgent:
    name: str = "coding"

    def run(self, state: TaskState, tools: ToolRegistry, memory: MemoryStore) -> TaskState:
        tool = tools.maybe_get("python_exec")
        summary = "No python execution tool is registered."
        code = ""
        if tool is None:
            state.results["status"] = "solver_unavailable"
            state.results["solver_summary"] = summary
            state = SolveSkill().run(state, tools)
            memory.set_agent_json(self.name, "solver_result", {"status": state.results.get("status"), "summary": summary})
            memory.append_event("agent", self.name, "done", {"stage": state.stage})
            return state

        try:
            summary, code = _build_llm_solver(state)
            result = tool.run(
                {
                    "code": code,
                    "filename": "solver.py",
                    "context": _build_solver_context(state),
                    "timeout_s": 20.0,
                }
            )
        except Exception as exc:
            summary, code = _build_fallback_solver_code(state)
            result = tool.run(
                {
                    "code": code,
                    "filename": "solver.py",
                    "context": _build_solver_context(state),
                    "timeout_s": 20.0,
                }
            )
            result["stderr"] = (result.get("stderr") or "") + f"\nRecovered from CODING generation failure: {exc}"

        solver_run = SolverRun(
            subproblem_title="overall_problem",
            success=bool(result.get("success")),
            summary=summary,
            code=code,
            stdout=str(result.get("stdout") or ""),
            stderr=str(result.get("stderr") or ""),
            artifacts=[str(name) for name in result.get("artifacts") or []],
        )
        state.solver_runs.append(solver_run)
        state.artifacts.extend(_load_solver_artifacts(str(result.get("run_dir") or ""), solver_run.artifacts))

        summary_lines = [summary]
        if solver_run.stdout.strip():
            summary_lines.append(solver_run.stdout.strip())
        state.results["status"] = "solved" if solver_run.success else "solver_failed"
        state.results["solver_summary"] = "\n".join(summary_lines).strip()
        state.results["solver_run_dir"] = result.get("run_dir")
        state = SolveSkill().run(state, tools)
        memory.set_agent_json(
            self.name,
            "solver_result",
            {
                "status": state.results.get("status"),
                "summary": state.results.get("solver_summary"),
                "artifacts": solver_run.artifacts,
                "run_dir": result.get("run_dir"),
            },
        )
        memory.append_event("agent", self.name, "done", {"stage": state.stage})
        return state


@dataclass(frozen=True)
class ReviewAgent:
    name: str = "review"

    def run(self, state: TaskState, tools: ToolRegistry, memory: MemoryStore) -> TaskState:
        state = ValidateSkill().run(state, tools)

        findings: list[dict[str, str]] = []
        for subproblem in state.subproblems:
            analysis = subproblem.analysis
            if not analysis.objective:
                _append_finding(
                    findings,
                    severity="medium",
                    area=subproblem.title,
                    message=f"{subproblem.title} 缺少明确目标描述。",
                    suggestion="补写目标函数或至少补写本子问题的输出目标。",
                )
            if not analysis.chosen_method:
                _append_finding(
                    findings,
                    severity="medium",
                    area=subproblem.title,
                    message=f"{subproblem.title} 还没有选定主方法。",
                    suggestion="从候选模型中选一个主方法，并说明为什么选它。",
                )
            if not analysis.constraints:
                _append_finding(
                    findings,
                    severity="low",
                    area=subproblem.title,
                    message=f"{subproblem.title} 还没有整理出约束条件。",
                    suggestion="把题面里的硬约束和软约束整理成列表。",
                )

        if not state.solver_runs:
            _append_finding(
                findings,
                severity="high",
                area="coding",
                message="还没有任何实际求解或执行记录。",
                suggestion="先让 Coding 阶段生成并执行至少一次求解脚本。",
            )
        else:
            for solver_run in state.solver_runs:
                if not solver_run.success:
                    _append_finding(
                        findings,
                        severity="high",
                        area="coding",
                        message=f"求解脚本运行失败：{solver_run.summary}",
                        suggestion="检查代码报错、输入数据和运行目录里的产物。",
                    )

        if state.report_md is not None:
            for section in _required_report_sections():
                if section not in state.report_md:
                    _append_finding(
                        findings,
                        severity="medium",
                        area="writing",
                        message=f"报告缺少章节：{section}",
                        suggestion="补齐标准论文结构，尤其是结果与结论部分。",
                    )
            placeholder_markers = ["待补充", "待确认", "TODO", "当前没有形成稳定的定量结果"]
            if any(marker in state.report_md for marker in placeholder_markers):
                _append_finding(
                    findings,
                    severity="medium",
                    area="writing",
                    message="报告中仍存在占位内容或未完成说明。",
                    suggestion="在正式提交前补齐数值结果、图表和最终结论。",
                )
            for subproblem in state.subproblems:
                if subproblem.title not in state.report_md:
                    _append_finding(
                        findings,
                        severity="low",
                        area="writing",
                        message=f"报告中没有明确提到 {subproblem.title}。",
                        suggestion="确保每个子问题都有单独的分析与结论段落。",
                    )

        review_notes = list(state.results.get("review_notes", []))
        if findings:
            review_notes.append(f"共识别出 {len(findings)} 条审稿提示。")
        else:
            review_notes.append("未发现明显结构性问题。")

        state.results["review_findings"] = findings
        state.results["review_notes"] = review_notes
        if state.report_md is None:
            state.results["reviewed_solution"] = True
            state.stage = "report"
        else:
            state.results["report_checks"] = _required_report_sections()
            state.results["final_review_done"] = True
            state.stage = "done"

        memory.set_agent_json(
            self.name,
            "review",
            {
                "checks": state.results.get("checks", []),
                "notes": review_notes,
                "report_checks": state.results.get("report_checks", []),
                "findings": findings,
            },
        )
        memory.append_event("agent", self.name, "done", {"stage": state.stage})
        return state


@dataclass(frozen=True)
class WritingAgent:
    name: str = "writing"

    def run(self, state: TaskState, tools: ToolRegistry, memory: MemoryStore) -> TaskState:
        cfg = load_llm_config("WRITING")
        if cfg is not None:
            llm = build_llm(cfg)
            try:
                report = llm.chat(
                    [
                        Message(role="system", content=render_prompt("writing_system")),
                        Message(
                            role="user",
                            content=render_prompt(
                                "writing_user",
                                problem_text=state.problem_text,
                                subproblems_json=json.dumps(_subproblems_payload(state), ensure_ascii=False, indent=2),
                                solver_runs_json=json.dumps(
                                    [
                                        {
                                            "subproblem_title": run.subproblem_title,
                                            "success": run.success,
                                            "summary": run.summary,
                                            "stdout": run.stdout,
                                            "stderr": run.stderr,
                                            "artifacts": run.artifacts,
                                        }
                                        for run in state.solver_runs
                                    ],
                                    ensure_ascii=False,
                                    indent=2,
                                ),
                                review_findings_json=json.dumps(
                                    state.results.get("review_findings", []),
                                    ensure_ascii=False,
                                    indent=2,
                                ),
                            ),
                        ),
                    ],
                    temperature=0.2,
                )
                state.report_md = report.strip()
            except Exception as exc:
                memory.set_agent_json(self.name, "llm_error", {"error": str(exc)})
                memory.append_event("agent", self.name, "llm_error", {"error": str(exc)})
                state = ReportSkill().run(state, tools)
        else:
            state = ReportSkill().run(state, tools)

        if state.report_md is not None:
            memory.set_shared("report_md", state.report_md)
            state.stage = "review"
        memory.append_event("agent", self.name, "done", {"stage": state.stage})
        return state
