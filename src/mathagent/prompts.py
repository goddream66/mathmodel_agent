from __future__ import annotations

from pathlib import Path


_PROMPT_DIR = Path(__file__).resolve().parents[2] / "templates" / "prompts"

_DEFAULT_PROMPTS: dict[str, str] = {
    "modeling_system": (
        "You are an expert in mathematical modeling competitions. "
        "Break the problem into sub-problems and provide structured analysis. "
        "Return JSON only."
    ),
    "modeling_user": (
        "Problem statement:\n"
        "{problem_text}\n\n"
        "Return a JSON array. Each item should include:\n"
        "- title: string\n"
        "- text: string\n"
        "- task_types: string[]\n"
        "- candidate_models: string[]\n"
        "- solution_plan: string[]\n"
        "- key_variables: string[]\n"
        "- needed_data: string[]\n"
        "- evaluation: string[]\n"
        "- notes: string[]\n"
        "If the problem should not be split, still return an array with one item. "
        "Do not include any commentary outside the JSON."
    ),
    "writing_system": (
        "You are an expert writer for mathematical modeling competition papers. "
        "Write a rigorous Markdown draft based on the problem statement and the "
        "sub-problem analysis. Do not fabricate numerical results. If data or "
        "experiments are missing, clearly state what needs to be verified."
    ),
    "writing_user": (
        "Problem statement:\n"
        "{problem_text}\n\n"
        "Sub-problem analysis (JSON):\n"
        "{subproblems_json}\n\n"
        "Write Markdown with the following sections:\n"
        "- Abstract\n"
        "- Problem Restatement\n"
        "- Sub-problem Analysis and Method Selection\n"
        "- Assumptions and Notation\n"
        "- Model Formulation and Solution\n"
        "- Results and Analysis\n"
        "- Conclusion and Future Work\n"
        "Explain the model or algorithm and the solution steps for each sub-problem."
    ),
}


def load_prompt(name: str) -> str:
    path = _PROMPT_DIR / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()

    if name not in _DEFAULT_PROMPTS:
        raise KeyError(f"Unknown prompt template: {name}")
    return _DEFAULT_PROMPTS[name].strip()


def render_prompt(name: str, **kwargs: str) -> str:
    return load_prompt(name).format(**kwargs)
