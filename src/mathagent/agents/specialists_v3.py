from __future__ import annotations

import ast
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
from ..reporting import inject_figure_titles, required_report_titles
from ..solvers import build_fallback_solver_code as builtin_build_fallback_solver_code
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
from ..verification.checkers import (
    build_report_sources,
    build_verification_findings,
    build_verification_summary,
)


RESULT_STATUS_VALUES = {"ok", "partial", "failed"}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        clean = str(item).strip()
        if clean:
            items.append(clean)
    return items


def _figure_titles(value: Any) -> list[str]:
    return _string_list(value)


_PLACEHOLDER_TEXT_MARKERS = (
    "formal constraints still need to be written explicitly",
    "constraints still need to be written",
    "placeholder",
    "todo",
    "tbd",
)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _is_placeholder_text(value: Any) -> bool:
    text = _clean_text(value).lower()
    if not text:
        return True
    return any(marker in text for marker in _PLACEHOLDER_TEXT_MARKERS)


def _clean_constraints(value: Any) -> list[str]:
    constraints = _string_list(value)
    return [item for item in constraints if not _is_placeholder_text(item)]


def _prefer_existing_title(candidate_title: str, fallback_title: str) -> str:
    title = candidate_title.strip()
    if not title:
        return fallback_title
    normalized = title.lower()
    if re.fullmatch(r"(subproblem|problem)\s*\d+", normalized):
        return fallback_title
    return title


def _has_baseline_structured_solver_marker(structured_result: dict[str, Any]) -> bool:
    evidence = [str(item).strip() for item in structured_result.get("evidence", []) if str(item).strip()]
    return "template_used=baseline_structured_solver" in evidence


def _subproblem_payload(subproblem: SubProblem) -> dict[str, Any]:
    return {
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


def _subproblems_payload(state: TaskState) -> list[dict[str, Any]]:
    return [_subproblem_payload(subproblem) for subproblem in state.subproblems]


def _solver_runs_payload(state: TaskState) -> list[dict[str, Any]]:
    return [
        {
            "subproblem_title": run.subproblem_title,
            "success": run.success,
            "summary": run.summary,
            "stdout": run.stdout,
            "stderr": run.stderr,
            "artifacts": run.artifacts,
            "schema_valid": run.schema_valid,
            "structured_result": run.structured_result,
        }
        for run in state.solver_runs
    ]


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
        elif suffix in {".png", ".jpg", ".jpeg", ".svg"}:
            payload = {"path": str(artifact_path), "name": artifact_name}
            kind = "figure"
        elif suffix == ".py":
            payload = artifact_path.read_text(encoding="utf-8", errors="replace")
            kind = "code"
        else:
            payload = artifact_path.read_text(encoding="utf-8", errors="replace")
            kind = "text"
        artifacts.append(ExperimentArtifact(name=artifact_name, kind=kind, payload=payload))
    return artifacts


def _build_solver_context(state: TaskState, subproblem: SubProblem, index: int) -> dict[str, Any]:
    return {
        "problem_text": state.problem_text,
        "clarifications": state.clarifications,
        "subproblem_index": index,
        "subproblem": _subproblem_payload(subproblem),
        "all_subproblems": _subproblems_payload(state),
        "input_data": state.input_data,
        "model": {
            "assumptions": state.model.assumptions,
            "constraints": state.model.constraints,
            "method_candidates": state.model.method_candidates,
            "chosen_method": state.model.chosen_method,
            "formulation_outline": state.model.formulation_outline,
            "evidence_gaps": state.model.evidence_gaps,
        },
    }


def _extract_code_block(text: str) -> str:
    match = re.search(r"```python\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def _normalize_numeric_results(value: Any) -> dict[str, float | int | str]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, float | int | str] = {}
    for key, raw in value.items():
        clean_key = str(key).strip()
        if not clean_key:
            continue
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            normalized[clean_key] = raw
        else:
            normalized[clean_key] = str(raw).strip()
    return normalized


def _synthesize_evidence(normalized: dict[str, Any]) -> list[str]:
    evidence = _string_list(normalized.get("evidence"))
    if evidence:
        return evidence

    synthesized = ["auto_evidence=synthesized_from_available_outputs"]
    numeric_results = normalized.get("numeric_results") or {}
    if isinstance(numeric_results, dict) and numeric_results:
        numeric_keys = list(numeric_results.keys())[:4]
        synthesized.append(f"numeric_result_keys={','.join(numeric_keys)}")
    figure_titles = _figure_titles(normalized.get("figure_titles"))
    if figure_titles:
        synthesized.append(f"figure_title={figure_titles[0]}")
    artifacts = _string_list(normalized.get("artifacts"))
    if artifacts:
        synthesized.append(f"artifact_names={','.join(artifacts[:3])}")
    status = str(normalized.get("status") or "").strip().lower()
    if status:
        synthesized.append(f"result_status={status}")
    method = str(normalized.get("method") or "").strip()
    if method:
        synthesized.append(f"method_marker={method}")
    summary = str(normalized.get("result_summary") or "").strip()
    if summary and len(synthesized) == 1:
        synthesized.append(f"summary_marker={summary[:120]}")
    return [item for item in synthesized if item]


def _validate_result_schema(payload: Any, expected_title: str) -> tuple[bool, dict[str, Any], str]:
    if not isinstance(payload, dict):
        return False, {}, "structured result is not a JSON object"

    normalized = {
        "subproblem_title": str(payload.get("subproblem_title") or "").strip(),
        "status": str(payload.get("status") or "").strip().lower(),
        "method": str(payload.get("method") or "").strip(),
        "objective": str(payload.get("objective") or "").strip(),
        "assumptions": _string_list(payload.get("assumptions")),
        "constraints": _clean_constraints(payload.get("constraints")),
        "result_summary": str(payload.get("result_summary") or "").strip(),
        "evidence": _string_list(payload.get("evidence")),
        "numeric_results": _normalize_numeric_results(payload.get("numeric_results")),
        "figure_titles": _figure_titles(payload.get("figure_titles")),
        "artifacts": _string_list(payload.get("artifacts")),
        "next_steps": _string_list(payload.get("next_steps")),
    }
    normalized["evidence"] = _synthesize_evidence(normalized)

    if not normalized["subproblem_title"]:
        return False, normalized, "missing subproblem_title"
    if normalized["subproblem_title"] != expected_title:
        return False, normalized, "subproblem_title does not match current subproblem"
    if normalized["status"] not in RESULT_STATUS_VALUES:
        return False, normalized, "status must be one of ok/partial/failed"
    if not normalized["method"]:
        return False, normalized, "missing method"
    if not normalized["result_summary"]:
        return False, normalized, "missing result_summary"
    if not normalized["evidence"]:
        return False, normalized, "evidence must contain at least one item"
    return True, normalized, ""


def _extract_json_candidate(stdout_text: str) -> Any:
    last_line = stdout_text.splitlines()[-1]
    try:
        return json.loads(last_line)
    except Exception:
        return extract_first_json(stdout_text)


def _extract_structured_result(run_dir: str, artifacts: list[str], stdout: str, expected_title: str) -> tuple[bool, dict[str, Any], str]:
    base_path = Path(run_dir)
    if "result.json" in artifacts:
        candidate = base_path / "result.json"
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception as exc:
            return False, {}, f"failed to parse result.json: {exc}"
        return _validate_result_schema(payload, expected_title)

    stdout_text = stdout.strip()
    if stdout_text:
        try:
            payload = _extract_json_candidate(stdout_text)
        except Exception:
            return False, {}, "missing result.json and stdout is not valid JSON"
        return _validate_result_schema(payload, expected_title)
    return False, {}, "missing result.json and empty stdout"


def _code_is_syntax_valid(code: str) -> tuple[bool, str]:
    source = code.strip()
    if not source:
        return False, "generated code is empty"
    try:
        ast.parse(source)
    except SyntaxError as exc:
        location = f"line {exc.lineno}" if exc.lineno else "unknown line"
        detail = exc.msg or "invalid syntax"
        return False, f"{detail} at {location}"
    return True, ""


def _should_retry_with_fallback(*, code: str, fallback_code: str, run_success: bool, schema_valid: bool, stderr: str, schema_error: str) -> bool:
    if code == fallback_code:
        return False
    if run_success and schema_valid:
        return False
    combined = "\n".join(part for part in [stderr, schema_error] if part).lower()
    retry_markers = (
        "syntaxerror",
        "invalid syntax",
        "unterminated string literal",
        "indentationerror",
        "typeerror: list.append() takes no keyword arguments",
        "missing result.json",
        "failed to parse result.json",
    )
    return any(marker in combined for marker in retry_markers)



def _build_fallback_solver_code(context: dict[str, Any]) -> tuple[str, str]:
    return builtin_build_fallback_solver_code(context)


def _build_llm_solver(state: TaskState, subproblem: SubProblem, index: int) -> tuple[str, str]:
    context = _build_solver_context(state, subproblem, index)
    fallback_summary, fallback_code = _build_fallback_solver_code(context)
    cfg = load_llm_config("CODING")
    if cfg is None:
        return fallback_summary, fallback_code

    llm = build_llm(cfg)
    response = llm.chat(
        [
            Message(role="system", content=render_prompt("coding_system")),
            Message(
                role="user",
                content=render_prompt(
                    "coding_user",
                    problem_text=state.problem_text,
                    context_json=json.dumps(context, ensure_ascii=False, indent=2),
                ),
            ),
        ],
        temperature=0.1,
    )
    try:
        payload = extract_first_json(response)
        if isinstance(payload, dict):
            summary = str(payload.get("summary") or "").strip() or f"Generated solver for {subproblem.title}."
            code = _extract_code_block(str(payload.get("code") or ""))
            if code:
                is_valid, syntax_error = _code_is_syntax_valid(code)
                if is_valid:
                    return summary, code
                return (
                    f"{fallback_summary} Fallback was used because generated code had invalid syntax: {syntax_error}.",
                    fallback_code,
                )
    except Exception:
        pass

    code = _extract_code_block(response)
    if code:
        is_valid, syntax_error = _code_is_syntax_valid(code)
        if is_valid:
            return f"Generated solver for {subproblem.title}.", code
        return (
            f"{fallback_summary} Fallback was used because generated code had invalid syntax: {syntax_error}.",
            fallback_code,
        )
    return fallback_summary, fallback_code


def _required_report_sections() -> list[str]:
    return required_report_titles()


def _append_finding(findings: list[dict[str, str]], *, severity: str, area: str, message: str, suggestion: str) -> None:
    findings.append(
        {
            "severity": severity,
            "area": area,
            "message": message,
            "suggestion": suggestion,
        }
    )


def _dedupe_findings(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    output: list[dict[str, str]] = []
    for finding in findings:
        key = (
            str(finding.get("severity") or ""),
            str(finding.get("area") or ""),
            str(finding.get("message") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(finding)
    return output


def _summarize_solver_runs(runs: list[SolverRun]) -> str:
    if not runs:
        return "No solver runs were produced."
    lines: list[str] = []
    for run in runs:
        status = run.structured_result.get("status") or "invalid"
        summary = run.structured_result.get("result_summary") or run.summary
        lines.append(f"{run.subproblem_title}: {status} - {summary}")
    return "\n".join(lines)


def _overall_solver_status(runs: list[SolverRun]) -> str:
    if not runs:
        return "solver_failed"
    if any(not run.success or not run.schema_valid for run in runs):
        return "solver_failed"
    statuses = {str(run.structured_result.get("status") or "") for run in runs}
    if statuses == {"ok"}:
        return "solved"
    if "failed" in statuses:
        return "solver_failed"
    return "partially_solved"


def _split_top_level_sections(markdown: str) -> list[list[str]]:
    if not markdown.strip():
        return []
    sections: list[list[str]] = []
    current: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("# "):
            if current:
                sections.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append(current)
    return sections


def _upsert_report_section(markdown: str, heading: str, content: str, marker: str) -> str:
    content = content.strip()
    if not content:
        return markdown.strip()

    sections = _split_top_level_sections(markdown)
    if not sections:
        return f"{heading}\n{content}".strip()

    updated_sections: list[str] = []
    inserted = False
    for section_lines in sections:
        section_text = "\n".join(section_lines).rstrip()
        if section_lines[0].strip() == heading:
            if marker and marker in section_text:
                updated_sections.append(section_text)
            else:
                updated_sections.append((section_text + "\n\n" + content).strip())
            inserted = True
        else:
            updated_sections.append(section_text)
    if not inserted:
        updated_sections.append(f"{heading}\n{content}".strip())
    return "\n\n".join(part for part in updated_sections if part).strip()


def _format_key_value_bullets(data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for key, value in data.items():
        lines.append(f"- {key}: {value}")
    return lines


def _build_analysis_alignment_block(state: TaskState) -> str:
    lines = ["## Structured Subproblem Alignment"]
    for subproblem in state.subproblems:
        analysis = subproblem.analysis
        lines.extend(
            [
                f"### {subproblem.title}",
                f"- objective: {analysis.objective or 'pending'}",
                f"- chosen_method: {analysis.chosen_method or 'pending'}",
            ]
        )
        constraints = analysis.constraints or ["pending_constraint"]
        lines.extend(f"- constraint: {item}" for item in constraints)
        lines.append("")
    return "\n".join(lines).strip()


def _build_solving_alignment_block(state: TaskState) -> str:
    lines = ["## Structured Solver Runs"]
    if not state.solver_runs:
        lines.append("- No solver runs were produced yet.")
        return "\n".join(lines)

    for run in state.solver_runs:
        structured = run.structured_result
        lines.extend(
            [
                f"### {run.subproblem_title}",
                f"- status: {structured.get('status', 'unknown')}",
                f"- method: {structured.get('method', 'unknown')}",
                f"- result_summary: {structured.get('result_summary', run.summary)}",
            ]
        )
        evidence = [str(item) for item in structured.get("evidence", []) if str(item).strip()]
        if evidence:
            lines.extend(f"- evidence: {item}" for item in evidence[:6])
        if run.artifacts:
            lines.extend(f"- artifact: {item}" for item in run.artifacts[:6])
        lines.append("")
    return "\n".join(lines).strip()


def _build_results_alignment_block(state: TaskState) -> str:
    lines = ["## Structured Results Alignment"]
    if not state.solver_runs:
        lines.append("- No structured results are available yet.")
        return "\n".join(lines)

    for run in state.solver_runs:
        structured = run.structured_result
        lines.append(f"### {run.subproblem_title}")
        lines.append(f"- status: {structured.get('status', 'unknown')}")
        numeric_results = dict(structured.get("numeric_results", {}))
        if numeric_results:
            lines.extend(_format_key_value_bullets(numeric_results))
        evidence = [str(item) for item in structured.get("evidence", []) if str(item).strip()]
        if evidence:
            lines.extend(f"- evidence: {item}" for item in evidence[:8])
        figure_titles = [str(item) for item in structured.get("figure_titles", []) if str(item).strip()]
        if figure_titles:
            lines.extend(f"- figure_title: {item}" for item in figure_titles)
        lines.append("")
    return "\n".join(lines).strip()


def _build_conclusion_alignment_block(state: TaskState) -> str:
    solved = state.results.get("solved_subproblems", [])
    partial = state.results.get("partial_subproblems", [])
    lines = ["## Review Conclusion"]
    lines.append(f"- solved_subproblems: {', '.join(solved) if solved else 'none'}")
    lines.append(f"- partial_subproblems: {', '.join(partial) if partial else 'none'}")
    lines.append(f"- solver_status: {state.results.get('status', 'unknown')}")
    return "\n".join(lines)


def _stabilize_report_markdown(markdown: str, state: TaskState) -> str:
    titles = required_report_titles()
    report = markdown.strip()
    if not report:
        report = f"{titles[0]}\nPending report generation."

    report = _upsert_report_section(
        report,
        titles[2],
        _build_analysis_alignment_block(state),
        "## Structured Subproblem Alignment",
    )
    report = _upsert_report_section(
        report,
        titles[4],
        _build_solving_alignment_block(state),
        "## Structured Solver Runs",
    )
    report = _upsert_report_section(
        report,
        titles[5],
        _build_results_alignment_block(state),
        "## Structured Results Alignment",
    )
    report = _upsert_report_section(
        report,
        titles[6],
        _build_conclusion_alignment_block(state),
        "## Review Conclusion",
    )
    return report.strip()


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
                existing_titles = [subproblem.title for subproblem in state.subproblems]
                payload = extract_first_json(
                    llm.chat(
                        [
                            Message(role="system", content=render_prompt("modeling_system")),
                            Message(
                                role="user",
                                content=render_prompt(
                                    "modeling_user",
                                    problem_text=state.problem_text,
                                    existing_subproblems_json=json.dumps(
                                        _subproblems_payload(state),
                                        ensure_ascii=False,
                                        indent=2,
                                    ),
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
                        fallback_title = existing_titles[index - 1] if index - 1 < len(existing_titles) else f"Subproblem {index}"
                        subproblem = SubProblem(
                            title=_prefer_existing_title(str(item.get("title") or "").strip(), fallback_title),
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
                        analysis.constraints = _clean_constraints(item.get("constraints"))
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
        if tool is None:
            state.results["status"] = "solver_unavailable"
            state.results["solver_summary"] = "No python execution tool is registered."
            state = SolveSkill().run(state, tools)
            memory.set_agent_json(
                self.name,
                "solver_result",
                {"status": state.results.get("status"), "summary": state.results.get("solver_summary")},
            )
            memory.append_event("agent", self.name, "done", {"stage": state.stage})
            return state

        state.solver_runs = []
        structured_results: list[dict[str, Any]] = []
        for index, subproblem in enumerate(state.subproblems, start=1):
            context = _build_solver_context(state, subproblem, index)
            fallback_summary, fallback_code = _build_fallback_solver_code(context)
            generation_error = ""
            try:
                summary, code = _build_llm_solver(state, subproblem, index)
            except Exception as exc:
                summary, code = fallback_summary, fallback_code
                generation_error = str(exc)

            result = tool.run(
                {
                    "code": code,
                    "filename": f"solver_{index}.py",
                    "context": context,
                    "timeout_s": 20.0,
                }
            )
            run_success = bool(result.get("success"))
            schema_valid, structured_result, schema_error = _extract_structured_result(
                str(result.get("run_dir") or ""),
                [str(name) for name in result.get("artifacts") or []],
                str(result.get("stdout") or ""),
                subproblem.title,
            )
            stderr_text = str(result.get("stderr") or "")
            if generation_error:
                stderr_text = (stderr_text + f"\nRecovered from CODING generation failure: {generation_error}").strip()

            if _should_retry_with_fallback(
                code=code,
                fallback_code=fallback_code,
                run_success=run_success,
                schema_valid=schema_valid,
                stderr=stderr_text,
                schema_error=schema_error,
            ):
                fallback_result = tool.run(
                    {
                        "code": fallback_code,
                        "filename": f"solver_{index}_fallback.py",
                        "context": context,
                        "timeout_s": 20.0,
                    }
                )
                fallback_run_success = bool(fallback_result.get("success"))
                fallback_schema_valid, fallback_structured_result, fallback_schema_error = _extract_structured_result(
                    str(fallback_result.get("run_dir") or ""),
                    [str(name) for name in fallback_result.get("artifacts") or []],
                    str(fallback_result.get("stdout") or ""),
                    subproblem.title,
                )
                if fallback_run_success or fallback_schema_valid:
                    stderr_parts = [stderr_text, "Retried with fallback solver after CODING execution failure."]
                    fallback_stderr = str(fallback_result.get("stderr") or "")
                    if fallback_stderr:
                        stderr_parts.append(f"Fallback stderr: {fallback_stderr}")
                    if fallback_schema_error:
                        stderr_parts.append(f"Fallback schema validation failed: {fallback_schema_error}")
                    stderr_text = "\n".join(part for part in stderr_parts if part).strip()
                    result = fallback_result
                    run_success = fallback_run_success
                    schema_valid = fallback_schema_valid
                    structured_result = fallback_structured_result
                    schema_error = fallback_schema_error
                    summary = f"{fallback_summary} Retried automatically after CODING execution failed."
                    code = fallback_code

            if not run_success and not structured_result:
                structured_result = {
                    "subproblem_title": subproblem.title,
                    "status": "failed",
                    "method": subproblem.analysis.chosen_method or "unknown",
                    "objective": subproblem.analysis.objective or "",
                    "assumptions": subproblem.analysis.assumptions,
                    "constraints": subproblem.analysis.constraints,
                    "result_summary": "Execution failed before a structured result was produced.",
                    "evidence": ["python_exec returned a non-zero exit status"],
                    "numeric_results": {},
                    "figure_titles": [],
                    "artifacts": [str(name) for name in result.get("artifacts") or []],
                    "next_steps": ["Inspect stderr and generated code before retrying."],
                }

            solver_run = SolverRun(
                subproblem_title=subproblem.title,
                success=run_success and schema_valid and structured_result.get("status") in {"ok", "partial"},
                summary=summary,
                code=code,
                stdout=str(result.get("stdout") or ""),
                stderr=(stderr_text + (f"\nSchema validation failed: {schema_error}" if schema_error else "")).strip(),
                artifacts=[str(name) for name in result.get("artifacts") or []],
                structured_result=structured_result,
                schema_valid=schema_valid,
            )
            state.solver_runs.append(solver_run)
            structured_results.append(structured_result)
            state.artifacts.extend(_load_solver_artifacts(str(result.get("run_dir") or ""), solver_run.artifacts))

        state.results["structured_solver_results"] = structured_results
        state.results["status"] = _overall_solver_status(state.solver_runs)
        state.results["solver_summary"] = _summarize_solver_runs(state.solver_runs)
        state.results["solved_subproblems"] = [
            run.subproblem_title
            for run in state.solver_runs
            if run.schema_valid and run.structured_result.get("status") == "ok"
        ]
        state.results["partial_subproblems"] = [
            run.subproblem_title
            for run in state.solver_runs
            if run.schema_valid and run.structured_result.get("status") == "partial"
        ]
        state = SolveSkill().run(state, tools)
        memory.set_agent_json(
            self.name,
            "solver_result",
            {
                "status": state.results.get("status"),
                "summary": state.results.get("solver_summary"),
                "runs": _solver_runs_payload(state),
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
                    message=f"{subproblem.title} is missing an explicit objective.",
                    suggestion="Add a clear objective or target output for this subproblem.",
                )
            if not analysis.chosen_method:
                _append_finding(
                    findings,
                    severity="medium",
                    area=subproblem.title,
                    message=f"{subproblem.title} does not have a chosen primary method.",
                    suggestion="Pick one main method from the candidate list and justify it.",
                )
            if not analysis.constraints:
                _append_finding(
                    findings,
                    severity="medium",
                    area=subproblem.title,
                    message=f"{subproblem.title} still lacks explicit constraints.",
                    suggestion="Translate hard and soft constraints from the problem statement into a list.",
                )

        if not state.solver_runs:
            _append_finding(
                findings,
                severity="high",
                area="coding",
                message="No executable solver runs were recorded.",
                suggestion="Run Coding again after improving the solver prompt or input data.",
            )
        else:
            for run in state.solver_runs:
                if not run.schema_valid:
                    _append_finding(
                        findings,
                        severity="high",
                        area="coding",
                        message=f"{run.subproblem_title} did not produce a valid structured result schema.",
                        suggestion="Require the generated code to write a valid result.json before marking success.",
                    )
                elif run.structured_result.get("status") == "partial":
                    _append_finding(
                        findings,
                        severity="medium",
                        area="coding",
                        message=f"{run.subproblem_title} only has a partial structured result.",
                        suggestion="Replace the baseline/fallback logic with a domain-specific solver or add more data.",
                    )
                elif run.structured_result.get("status") == "failed":
                    _append_finding(
                        findings,
                        severity="high",
                        area="coding",
                        message=f"{run.subproblem_title} returned a failed structured result.",
                        suggestion="Inspect the generated code, stderr, and result.json for this subproblem.",
                    )
                if _has_baseline_structured_solver_marker(run.structured_result):
                    _append_finding(
                        findings,
                        severity="high",
                        area="coding",
                        message=f"{run.subproblem_title} is still using baseline_structured_solver placeholder output.",
                        suggestion="Replace the generic baseline solver with a domain-specific solver before treating this subproblem as solved.",
                    )

        if state.report_md is not None:
            if "## " not in state.report_md:
                _append_finding(
                    findings,
                    severity="medium",
                    area="writing",
                    message="The report is missing detailed subsection headings.",
                    suggestion="Add per-subproblem subsections and a dedicated results section.",
                )
            for run in state.solver_runs:
                if run.subproblem_title not in state.report_md:
                    _append_finding(
                        findings,
                        severity="low",
                        area="writing",
                        message=f"The report does not explicitly mention {run.subproblem_title}.",
                        suggestion="Add a short paragraph summarizing the structured result for that subproblem.",
                    )

        review_notes = list(state.results.get("review_notes", []))
        verification_summary = build_verification_summary(state)
        report_sources = build_report_sources(state)
        findings.extend(build_verification_findings(state, verification_summary, report_sources))
        findings = _dedupe_findings(findings)
        if findings:
            review_notes.append(f"Identified {len(findings)} review findings.")
        else:
            review_notes.append("No major structural issues were detected.")

        state.results["review_findings"] = findings
        state.results["review_notes"] = review_notes
        state.results["verification_summary"] = verification_summary
        state.results["report_sources"] = report_sources
        if state.report_md is None:
            state.results["reviewed_solution"] = True
            state.stage = "report"
        else:
            state.results["report_checks"] = _required_report_sections()
            blocking_messages = {
                "The results section does not explicitly cite solver evidence markers.",
            }
            state.results["final_review_done"] = not any(
                str(finding.get("severity") or "").lower() == "high"
                or str(finding.get("message") or "") in blocking_messages
                for finding in findings
            )
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
                                solver_runs_json=json.dumps(_solver_runs_payload(state), ensure_ascii=False, indent=2),
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
                state.report_md = inject_figure_titles(_stabilize_report_markdown(report.strip(), state), state)
            except Exception as exc:
                memory.set_agent_json(self.name, "llm_error", {"error": str(exc)})
                memory.append_event("agent", self.name, "llm_error", {"error": str(exc)})
                state = ReportSkill().run(state, tools)
        else:
            state = ReportSkill().run(state, tools)

        if state.report_md is not None:
            state.report_md = inject_figure_titles(_stabilize_report_markdown(state.report_md, state), state)
            memory.set_shared("report_md", state.report_md)
            state.stage = "review"
        memory.append_event("agent", self.name, "done", {"stage": state.stage})
        return state

