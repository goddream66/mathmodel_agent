Problem statement:
{problem_text}

Return a JSON array. Each item should include:
- title: string
- text: string
- task_types: string[]
- candidate_models: string[]
- solution_plan: string[]
- key_variables: string[]
- needed_data: string[]
- evaluation: string[]
- notes: string[]
- objective: string
- constraints: string[]
- assumptions: string[]
- deliverables: string[]
- formulation_steps: string[]
- chosen_method: string
- confidence: number between 0 and 1

If the problem should not be split, still return an array with one item.
Do not include any commentary outside the JSON.
