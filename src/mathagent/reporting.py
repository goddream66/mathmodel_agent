from __future__ import annotations

import re
from dataclasses import dataclass

from .state import TaskState


@dataclass(frozen=True)
class ReportSectionSpec:
    key: str
    title: str
    aliases: tuple[str, ...]

    @property
    def heading(self) -> str:
        return f"# {self.title}"


REPORT_SECTION_SPECS: tuple[ReportSectionSpec, ...] = (
    ReportSectionSpec("abstract", "摘要", ("abstract", "summary", "摘要")),
    ReportSectionSpec(
        "problem",
        "问题重述",
        ("problem", "statement", "problem_statement", "问题", "问题重述", "题目"),
    ),
    ReportSectionSpec(
        "analysis",
        "子问题分析与方法选择",
        ("analysis", "method", "methods", "子问题", "分析", "方法"),
    ),
    ReportSectionSpec(
        "modeling",
        "模型假设与符号说明",
        ("model", "modeling", "assumptions", "symbols", "模型", "假设", "符号"),
    ),
    ReportSectionSpec(
        "solving",
        "求解与实验",
        ("solve", "solving", "experiment", "experiments", "求解", "实验"),
    ),
    ReportSectionSpec(
        "results",
        "结果与分析",
        ("result", "results", "finding", "findings", "结果", "分析"),
    ),
    ReportSectionSpec(
        "review",
        "审稿提示",
        ("review", "checks", "findings", "审稿", "提示"),
    ),
    ReportSectionSpec(
        "conclusion",
        "结论与后续工作",
        ("conclusion", "conclusions", "next", "discussion", "结论", "后续"),
    ),
)

_SECTION_BY_KEY = {spec.key: spec for spec in REPORT_SECTION_SPECS}
_SECTION_ALIASES = {
    alias.lower(): spec.key
    for spec in REPORT_SECTION_SPECS
    for alias in (spec.key, spec.title, *spec.aliases)
}


def available_report_sections() -> list[dict[str, str]]:
    return [{"key": spec.key, "title": spec.title} for spec in REPORT_SECTION_SPECS]


def required_report_titles() -> list[str]:
    return [
        _SECTION_BY_KEY["abstract"].heading,
        _SECTION_BY_KEY["problem"].heading,
        _SECTION_BY_KEY["analysis"].heading,
        _SECTION_BY_KEY["modeling"].heading,
        _SECTION_BY_KEY["solving"].heading,
        _SECTION_BY_KEY["results"].heading,
        _SECTION_BY_KEY["conclusion"].heading,
    ]


def resolve_report_sections(values: list[str] | None) -> list[str]:
    if not values:
        return []

    resolved: list[str] = []
    unknown: list[str] = []
    for raw in values:
        for token in _split_section_tokens(raw):
            lowered = token.lower()
            if lowered == "all":
                return []
            key = _SECTION_ALIASES.get(lowered)
            if key is None:
                unknown.append(token)
                continue
            if key not in resolved:
                resolved.append(key)
    if unknown:
        options = ", ".join(f"{spec.key}({spec.title})" for spec in REPORT_SECTION_SPECS)
        raise ValueError(f"Unknown report section: {', '.join(unknown)}. Available: {options}")
    return resolved


def select_report_sections(markdown: str, section_keys: list[str] | None) -> str:
    if not markdown.strip() or not section_keys:
        return markdown

    sections = _split_markdown_sections(markdown)
    if not sections:
        return markdown

    selected_blocks: list[str] = []
    wanted_keys = {key for key in section_keys if key in _SECTION_BY_KEY}
    for title, block in sections:
        resolved_key = _section_key_from_title(title)
        if resolved_key in wanted_keys:
            selected_blocks.append(block.rstrip())
    return "\n\n".join(selected_blocks).strip() or markdown


def inject_figure_titles(markdown: str, state: TaskState) -> str:
    entries: list[tuple[str, list[str]]] = []
    for run in state.solver_runs:
        titles = [
            str(item).strip()
            for item in run.structured_result.get("figure_titles", [])
            if str(item).strip()
        ]
        if titles:
            entries.append((run.subproblem_title, titles))

    if not entries:
        return markdown

    block_lines = ["## 图表标题"]
    for subproblem_title, titles in entries:
        block_lines.append(f"### {subproblem_title}")
        for index, title in enumerate(titles, start=1):
            block_lines.append(f"- 图{index}：{title}")
        block_lines.append("")
    block = "\n".join(block_lines).strip()

    sections = _split_markdown_sections(markdown)
    if not sections:
        return (markdown.rstrip() + "\n\n" + block).strip()

    updated_blocks: list[str] = []
    inserted = False
    for _, section_block in sections:
        lines = section_block.splitlines()
        heading = lines[0][2:].strip() if lines and lines[0].startswith("# ") else ""
        if not inserted and _section_key_from_title(heading) == "results":
            if "## 图表标题" in section_block:
                updated_blocks.append(section_block.rstrip())
            else:
                updated_blocks.append(section_block.rstrip() + "\n\n" + block)
            inserted = True
        else:
            updated_blocks.append(section_block.rstrip())

    if not inserted:
        updated_blocks.append(_SECTION_BY_KEY["results"].heading + "\n\n" + block)
    return "\n\n".join(part for part in updated_blocks if part).strip()


def render_fallback_report(state: TaskState) -> str:
    lines: list[str] = [
        _SECTION_BY_KEY["abstract"].heading,
        "This fallback report summarizes the current modeling plan, structured solver outputs, and review findings. It explicitly marks missing evidence instead of fabricating results.",
        "",
        _SECTION_BY_KEY["problem"].heading,
        state.problem_text.strip(),
        "",
        _SECTION_BY_KEY["analysis"].heading,
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
            _SECTION_BY_KEY["modeling"].heading,
            *_render_bullets(state.model.assumptions, empty_text="No global assumptions yet"),
            "",
            "## 建模主线",
            *_render_bullets(state.model.formulation_outline, empty_text="No global formulation outline yet"),
            "",
            _SECTION_BY_KEY["solving"].heading,
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
                figure_titles = [str(item) for item in structured.get("figure_titles", []) if str(item).strip()]
                if figure_titles:
                    lines.extend(["### Figure Titles", *_render_bullets(figure_titles), ""])
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
            _SECTION_BY_KEY["results"].heading,
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
            figure_titles = [str(x) for x in item.get("figure_titles", []) if str(x).strip()]
            if figure_titles:
                lines.extend(["#### Figure Titles", *_render_bullets(figure_titles)])
            lines.append("")

    findings = state.results.get("review_findings", [])
    if findings:
        lines.append(_SECTION_BY_KEY["review"].heading)
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
            _SECTION_BY_KEY["conclusion"].heading,
            "The current draft already links the problem decomposition, structured solver results, and review findings. Before submission, replace baseline template results with domain-specific computations where accuracy matters.",
        ]
    )
    return "\n".join(lines)


def _render_bullets(items: list[str], *, empty_text: str = "No details yet") -> list[str]:
    if not items:
        return [f"- {empty_text}"]
    return [f"- {item}" for item in items]


def _split_section_tokens(raw: str) -> list[str]:
    return [token.strip() for token in raw.replace(",", " ").split() if token.strip()]


def _normalize_section_title(title: str) -> str:
    normalized = title.strip()
    normalized = re.sub(
        r"^(?:第\s*[0-9一二三四五六七八九十百零]+\s*[章节部分篇]\s*|[0-9一二三四五六七八九十]+(?:\.[0-9]+)*\s*[、.．)]\s*)",
        "",
        normalized,
    )
    return normalized.strip()


def _section_key_from_title(title: str) -> str | None:
    normalized = _normalize_section_title(title).lower()
    candidates = (
        normalized,
        normalized.replace(" ", "_"),
        normalized.replace(" ", ""),
        normalized.replace("-", "_"),
    )
    for candidate in candidates:
        key = _SECTION_ALIASES.get(candidate)
        if key is not None:
            return key
    return None


def _split_markdown_sections(markdown: str) -> list[tuple[str, str]]:
    lines = markdown.splitlines()
    sections: list[tuple[str, str]] = []
    current_title = "__preface__"
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("# "):
            if current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = line[2:].strip()
            current_lines = [line]
            continue
        current_lines.append(line)

    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))
    return sections
