Problem statement:
{problem_text}

Structured context JSON:
{context_json}

Return a JSON object with:
- summary: short string
- code: Python source code as a string

Requirements:
- The code should be self-contained and executable.
- It may read context.json from the current directory.
- It must write result.json using the required schema.
- It should write at least one additional artifact file summarizing the computation.
- The generated code should solve the current subproblem only, not the whole task at once.
- Do not use markdown fences inside the JSON string unless unavoidable.
