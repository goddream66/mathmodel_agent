Problem statement:
{problem_text}

Sub-problem analysis (JSON):
{subproblems_json}

Solver runs (JSON):
{solver_runs_json}

Review findings (JSON):
{review_findings_json}

Write Markdown with the following top-level sections:
- 摘要
- 问题重述
- 子问题分析与方法选择
- 模型假设与符号说明
- 求解与实验
- 结果与分析
- 结论与后续工作

Requirements:
- Use the exact subproblem titles from subproblems_json as subsection titles.
- For each subproblem, explain the model, algorithm, and solution steps.
- For each subproblem, cite at least one numeric_results field or one evidence marker from the corresponding solver run.
- If figure_titles are present in a solver result, explicitly list those chart titles in the relevant section.
- If a solver run failed or evidence is missing, state that clearly instead of inventing results.
