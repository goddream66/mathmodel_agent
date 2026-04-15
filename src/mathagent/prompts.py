from __future__ import annotations

from pathlib import Path


_PROMPT_DIR = Path(__file__).resolve().parents[2] / "templates" / "prompts"


class _SafeFormatDict(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return ""


_DEFAULT_PROMPTS: dict[str, str] = {
    "modeling_system": (
        "You are an expert in mathematical modeling competitions. "
        "Break the problem into structured subproblems that can be solved and written into a paper. "
        "Return JSON only. Each subproblem must include an explicit objective, concrete constraints, "
        "assumptions, deliverables, formulation steps, a chosen method, and a confidence score. "
        "Do not leave placeholder text such as TODO or 'constraints still need to be written'."
    ),
    "modeling_user": (
        "Problem statement:\n"
        "{problem_text}\n\n"
        "Existing subproblems from the rule-based decomposition stage:\n"
        "{existing_subproblems_json}\n\n"
        "Return a JSON array. Each item must include:\n"
        "- title: string, and it should stay aligned with the existing decomposition whenever possible\n"
        "- text: string\n"
        "- task_types: string[]\n"
        "- candidate_models: string[]\n"
        "- solution_plan: string[]\n"
        "- key_variables: string[]\n"
        "- needed_data: string[]\n"
        "- evaluation: string[]\n"
        "- notes: string[]\n"
        "- objective: string\n"
        "- constraints: string[] with explicit hard/soft constraints, not placeholder text\n"
        "- assumptions: string[]\n"
        "- deliverables: string[]\n"
        "- formulation_steps: string[]\n"
        "- chosen_method: string\n"
        "- confidence: number between 0 and 1\n"
        "If the problem should not be split, still return an array with one item. "
        "Do not include any commentary outside the JSON."
    ),
    "coding_system": (
        "You are a coding agent for mathematical modeling. "
        "Return JSON only with fields 'summary' and 'code'. "
        "The code must be executable Python, read optional context from context.json, "
        "write useful artifacts to the current working directory, and write a result.json file with this schema: "
        "{{subproblem_title,status,method,objective,assumptions,constraints,"
        "result_summary,evidence,numeric_results,figure_titles,artifacts,next_steps}}. "
        "The status must be one of ok, partial, or failed. "
        "Prefer a domain-specific solver over generic text statistics. "
        "Do not emit placeholder evidence such as template_used=baseline_structured_solver unless the subproblem truly cannot be solved. "
        "If optional scientific libraries such as numpy, pandas, scipy, pulp, or networkx are available, you may use them. "
        "When meaningful, include backend code that writes one or more chart/image artifacts and record their titles in figure_titles."
    ),
    "coding_user": (
        "Problem statement:\n"
        "{problem_text}\n\n"
        "Structured context JSON:\n"
        "{context_json}\n\n"
        "Return a JSON object with:\n"
        "- summary: short string\n"
        "- code: Python source code as a string\n"
        "Requirements:\n"
        "- The code should be self-contained and executable.\n"
        "- It may read context.json from the current directory.\n"
        "- It must write result.json using the required schema.\n"
        "- It should write at least one additional artifact file summarizing the computation.\n"
        "- The generated code should solve the current subproblem only, not the whole task at once.\n"
        "- Reuse the constraints and objective from the structured context instead of inventing a different task.\n"
        "- If the problem is underspecified, report partial or failed honestly and explain what is missing.\n"
        "- Do not use markdown fences inside the JSON string unless unavoidable.\n"
    ),
    "writing_system": (
        "You are an expert writer for mathematical modeling competition papers. "
        "Write a rigorous Markdown draft based on the problem statement, the subproblem analysis, "
        "the solver outputs, and the review findings. "
        "Do not fabricate numerical results. "
        "Use the exact subproblem titles from the structured state instead of renaming them. "
        "Explicitly cite numeric_results and evidence from each structured solver result whenever available. "
        "If figure_titles are present, write those chart titles explicitly in the report body. "
        "If data or experiments are missing, say so clearly instead of pretending the computation is complete."
    ),
    "writing_user": (
        "Problem statement:\n"
        "{problem_text}\n\n"
        "Sub-problem analysis (JSON):\n"
        "{subproblems_json}\n\n"
        "Solver runs (JSON):\n"
        "{solver_runs_json}\n\n"
        "Review findings (JSON):\n"
        "{review_findings_json}\n\n"
        "Write Markdown with the following top-level sections:\n"
        "- 摘要\n"
        "- 问题重述\n"
        "- 子问题分析与方法选择\n"
        "- 模型假设与符号说明\n"
        "- 求解与实验\n"
        "- 结果与分析\n"
        "- 结论与后续工作\n"
        "Requirements:\n"
        "- Use the exact subproblem titles from subproblems_json as subsection titles.\n"
        "- For each subproblem, explain the model, algorithm, and solution steps.\n"
        "- For each subproblem, cite at least one numeric_results field or one evidence marker from the corresponding solver run.\n"
        "- If figure_titles are present in a solver result, explicitly list those chart titles in the relevant section.\n"
        "- If a solver run failed or evidence is missing, state that clearly instead of inventing results.\n"
    ),
}


def load_prompt(name: str) -> str:
    path = _PROMPT_DIR / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()

    if name not in _DEFAULT_PROMPTS:
        raise KeyError(f"Unknown prompt template: {name}")
    return _DEFAULT_PROMPTS[name].strip()


def render_prompt(name: str, **kwargs: object) -> str:
    return load_prompt(name).format_map(
        _SafeFormatDict({key: str(value) for key, value in kwargs.items()})
    )
