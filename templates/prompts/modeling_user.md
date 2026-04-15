Problem statement:
{problem_text}

Existing subproblems from the rule-based decomposition stage:
{existing_subproblems_json}

Return a JSON array. Each item must include:
- title: string, and it should stay aligned with the existing decomposition whenever possible
- text: string
- task_types: string[]
- candidate_models: string[]
- solution_plan: string[]
- key_variables: string[]
- needed_data: string[]
- evaluation: string[]
- notes: string[]
- objective: string
- constraints: string[] with explicit hard/soft constraints, not placeholder text
- assumptions: string[]
- deliverables: string[]
- formulation_steps: string[]
- chosen_method: string
- confidence: number between 0 and 1

If the problem should not be split, still return an array with one item.
Do not include any commentary outside the JSON.
