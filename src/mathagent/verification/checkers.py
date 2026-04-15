from __future__ import annotations

from typing import Any

from ..reporting import REPORT_SECTION_SPECS, extract_report_section
from ..state import TaskState


def build_verification_summary(state: TaskState) -> dict[str, Any]:
    subproblem_checks: list[dict[str, Any]] = []
    failed_checks = 0

    for subproblem in state.subproblems:
        analysis = subproblem.analysis
        missing_fields: list[str] = []
        if not analysis.objective:
            missing_fields.append("objective")
        if not analysis.constraints:
            missing_fields.append("constraints")
        if not analysis.chosen_method:
            missing_fields.append("chosen_method")
        verdict = "ok" if not missing_fields else "needs_attention"
        if missing_fields:
            failed_checks += 1
        subproblem_checks.append(
            {
                "title": subproblem.title,
                "verdict": verdict,
                "missing_fields": missing_fields,
            }
        )

    solver_checks: list[dict[str, Any]] = []
    for run in state.solver_runs:
        issues: list[str] = []
        if not run.schema_valid:
            issues.append("invalid_schema")
        if not run.success:
            issues.append("unsuccessful_run")
        if not run.structured_result.get("evidence"):
            issues.append("missing_evidence")
        verdict = "ok" if not issues else "needs_attention"
        if issues:
            failed_checks += 1
        solver_checks.append(
            {
                "subproblem_title": run.subproblem_title,
                "verdict": verdict,
                "issues": issues,
            }
        )

    report_sources = build_report_sources(state)
    tracked_sections = ("analysis", "solving", "results", "conclusion")
    uncited_subproblems = sorted(
        {
            title
            for key in tracked_sections
            for title in report_sources.get(key, {}).get("missing_subproblems", [])
        }
    )
    missing_required_sections = [
        key
        for key in _required_section_keys()
        if not report_sources.get(key, {}).get("present", False)
    ]
    if uncited_subproblems:
        failed_checks += len(uncited_subproblems)
    if state.report_md and missing_required_sections:
        failed_checks += len(missing_required_sections)

    return {
        "overall_verdict": "ok" if failed_checks == 0 else "needs_attention",
        "failed_check_count": failed_checks,
        "subproblem_checks": subproblem_checks,
        "solver_checks": solver_checks,
        "uncited_subproblems": uncited_subproblems,
        "missing_required_sections": missing_required_sections,
        "report_checks": {
            "section_count": sum(1 for value in report_sources.values() if value.get("present")),
            "required_section_count": len(_required_section_keys()),
            "missing_required_sections": missing_required_sections,
        },
    }


def build_report_sources(state: TaskState) -> dict[str, dict[str, Any]]:
    report_md = state.report_md or ""
    solver_titles = [run.subproblem_title for run in state.solver_runs]
    sources: dict[str, dict[str, Any]] = {}

    for spec in REPORT_SECTION_SPECS:
        section_text = extract_report_section(report_md, spec.key)
        referenced_subproblems = [title for title in solver_titles if title in section_text]
        referenced_artifacts = [
            artifact.name
            for artifact in state.artifacts
            if artifact.name and artifact.name in section_text
        ]
        evidence_markers: list[str] = []
        numeric_result_keys: list[str] = []
        for run in state.solver_runs:
            for evidence in run.structured_result.get("evidence", []):
                marker = str(evidence)
                if marker and marker in section_text and marker not in evidence_markers:
                    evidence_markers.append(marker)
            for key in dict(run.structured_result.get("numeric_results", {})).keys():
                marker = str(key)
                if marker and marker in section_text and marker not in numeric_result_keys:
                    numeric_result_keys.append(marker)
        missing_subproblems = [title for title in solver_titles if solver_titles and title not in referenced_subproblems]
        sources[spec.key] = {
            "heading": spec.heading,
            "present": bool(section_text.strip()),
            "referenced_subproblems": referenced_subproblems,
            "referenced_artifacts": referenced_artifacts,
            "evidence_markers": evidence_markers,
            "numeric_result_keys": numeric_result_keys,
            "referenced_subproblem_count": len(referenced_subproblems),
            "referenced_artifact_count": len(referenced_artifacts),
            "referenced_evidence_count": len(evidence_markers),
            "referenced_numeric_count": len(numeric_result_keys),
            "missing_subproblems": missing_subproblems,
        }

    return sources


def build_verification_findings(
    state: TaskState,
    verification_summary: dict[str, Any] | None = None,
    report_sources: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    verification_summary = verification_summary or build_verification_summary(state)
    report_sources = report_sources or build_report_sources(state)
    findings: list[dict[str, str]] = []

    for item in verification_summary.get("subproblem_checks", []):
        missing_fields = [str(field) for field in item.get("missing_fields", [])]
        if missing_fields:
            findings.append(
                {
                    "severity": "medium",
                    "area": str(item.get("title") or "modeling"),
                    "message": f"Missing core modeling fields: {', '.join(missing_fields)}.",
                    "suggestion": "Complete the objective, constraints, and chosen method before final submission.",
                }
            )

    for item in verification_summary.get("solver_checks", []):
        issues = [str(issue) for issue in item.get("issues", [])]
        if issues:
            findings.append(
                {
                    "severity": "high" if "invalid_schema" in issues else "medium",
                    "area": str(item.get("subproblem_title") or "coding"),
                    "message": f"Solver verification issues: {', '.join(issues)}.",
                    "suggestion": "Inspect the solver output, evidence list, and schema validity for this subproblem.",
                }
            )

    for title in verification_summary.get("uncited_subproblems", []):
        findings.append(
            {
                "severity": "medium",
                "area": "writing",
                "message": f"The report does not consistently cite evidence for {title}.",
                "suggestion": "Mention this subproblem in the relevant section and connect it to numeric results or evidence markers.",
            }
        )

    for key in verification_summary.get("missing_required_sections", []):
        findings.append(
            {
                "severity": "medium",
                "area": "writing",
                "message": f"Missing required report section: {key}.",
                "suggestion": "Restore all required sections before treating the draft as complete.",
            }
        )

    solving = report_sources.get("solving", {})
    if solving.get("present") and not (
        solving.get("referenced_evidence_count") or solving.get("referenced_numeric_count")
    ):
        findings.append(
            {
                "severity": "medium",
                "area": "writing",
                "message": "The solving section does not explicitly cite solver evidence markers.",
                "suggestion": "Reference evidence markers, numeric results, or generated artifacts directly in the solving section.",
            }
        )

    results = report_sources.get("results", {})
    if results.get("present") and not (
        results.get("referenced_evidence_count") or results.get("referenced_numeric_count")
    ):
        findings.append(
            {
                "severity": "high",
                "area": "writing",
                "message": "The results section does not explicitly cite solver evidence markers.",
                "suggestion": "Reference numeric results, artifacts, or evidence items directly in the results section.",
            }
        )

    return findings


def _required_section_keys() -> list[str]:
    return [spec.key for spec in REPORT_SECTION_SPECS if spec.key != "review"]
