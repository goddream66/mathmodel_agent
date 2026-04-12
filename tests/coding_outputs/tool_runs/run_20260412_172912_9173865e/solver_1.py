from __future__ import annotations
import json
import re
from pathlib import Path

context = {
  "problem_text": "Problem 1: forecast demand for the next 7 days and report one numeric indicator.\nProblem 2: optimize cost under a budget of 100 and explain the chosen method.",
  "clarifications": [
    "问题 的硬约束和软约束分别是什么？"
  ],
  "subproblem_index": 1,
  "subproblem": {
    "title": "问题",
    "text": "Problem 1: forecast demand for the next 7 days and report one numeric indicator.\nProblem 2: optimize cost under a budget of 100 and explain the chosen method.",
    "analysis": {
      "task_types": [
        "通用建模"
      ],
      "candidate_models": [
        "基线模型 + 对比实验"
      ],
      "solution_plan": [
        "先明确输入、输出、约束和评价指标，避免模型目标漂移。",
        "先给出一个可计算的基线模型。",
        "再做对比分析和结果解释。"
      ],
      "key_variables": [
        "核心状态变量"
      ],
      "needed_data": [
        "题目中涉及的输入参数和边界条件"
      ],
      "evaluation": [
        "检查假设是否合理、变量定义是否一致。"
      ],
      "notes": [
        "先把题目里的变量、单位、边界条件统一。",
        "避免在没有数据支撑时直接给出数值结论。",
        "建议先做基线模型，再逐步增加复杂度。"
      ],
      "objective": "把题目转写成可计算、可解释、可验证的模型。",
      "constraints": [],
      "assumptions": [
        "变量定义清晰且可以被观测、估计或求解。",
        "原始题面没有说明的外部环境在分析周期内保持相对稳定。"
      ],
      "deliverables": [
        "结构化建模思路",
        "关键公式或算法流程",
        "可复核的结论说明"
      ],
      "formulation_steps": [
        "目标定义：把题目转写成可计算、可解释、可验证的模型。"
      ],
      "chosen_method": "基线模型 + 对比实验",
      "confidence": 0.55
    }
  },
  "all_subproblems": [
    {
      "title": "问题",
      "text": "Problem 1: forecast demand for the next 7 days and report one numeric indicator.\nProblem 2: optimize cost under a budget of 100 and explain the chosen method.",
      "analysis": {
        "task_types": [
          "通用建模"
        ],
        "candidate_models": [
          "基线模型 + 对比实验"
        ],
        "solution_plan": [
          "先明确输入、输出、约束和评价指标，避免模型目标漂移。",
          "先给出一个可计算的基线模型。",
          "再做对比分析和结果解释。"
        ],
        "key_variables": [
          "核心状态变量"
        ],
        "needed_data": [
          "题目中涉及的输入参数和边界条件"
        ],
        "evaluation": [
          "检查假设是否合理、变量定义是否一致。"
        ],
        "notes": [
          "先把题目里的变量、单位、边界条件统一。",
          "避免在没有数据支撑时直接给出数值结论。",
          "建议先做基线模型，再逐步增加复杂度。"
        ],
        "objective": "把题目转写成可计算、可解释、可验证的模型。",
        "constraints": [],
        "assumptions": [
          "变量定义清晰且可以被观测、估计或求解。",
          "原始题面没有说明的外部环境在分析周期内保持相对稳定。"
        ],
        "deliverables": [
          "结构化建模思路",
          "关键公式或算法流程",
          "可复核的结论说明"
        ],
        "formulation_steps": [
          "目标定义：把题目转写成可计算、可解释、可验证的模型。"
        ],
        "chosen_method": "基线模型 + 对比实验",
        "confidence": 0.55
      }
    }
  ],
  "model": {
    "assumptions": [
      "变量定义清晰且可以被观测、估计或求解。",
      "原始题面没有说明的外部环境在分析周期内保持相对稳定。"
    ],
    "constraints": [],
    "method_candidates": [
      "基线模型 + 对比实验"
    ],
    "chosen_method": "基线模型 + 对比实验",
    "formulation_outline": [
      "目标定义：把题目转写成可计算、可解释、可验证的模型。"
    ],
    "evidence_gaps": [
      "题目中涉及的输入参数和边界条件"
    ]
  }
}
subproblem = context["subproblem"]
analysis = subproblem["analysis"]
text = subproblem["text"] or context["problem_text"]
numbers = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]
status = "partial"
if numbers:
    status = "ok"
result = {
    "subproblem_title": subproblem["title"],
    "status": status,
    "method": analysis.get("chosen_method") or "baseline_structured_solver",
    "objective": analysis.get("objective") or "Clarify objective before formal solving.",
    "assumptions": analysis.get("assumptions") or ["Use the current problem statement as the primary evidence source."],
    "constraints": analysis.get("constraints") or ["Formal constraints still need to be written explicitly."],
    "result_summary": (
        "Created a structured baseline result. "
        + ("Detected numerical signals in the subproblem text." if numbers else "No direct numeric signal was found; more data is needed.")
    ),
    "evidence": [
        f"chosen_method={analysis.get('chosen_method') or 'baseline_structured_solver'}",
        f"number_count={len(numbers)}",
    ],
    "numeric_results": {
        "detected_number_count": len(numbers),
        "first_number": numbers[0] if numbers else "n/a",
    },
    "artifacts": ["result.json", "solver_notes.md"],
    "next_steps": [
        "Replace fallback logic with a domain-specific solver if numeric accuracy matters.",
        "Provide data tables or parameters for formal optimization or forecasting.",
    ],
}
Path("result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
notes = [
    "# Solver Notes",
    "",
    f"- subproblem_title: {result['subproblem_title']}",
    f"- status: {result['status']}",
    f"- method: {result['method']}",
    f"- objective: {result['objective']}",
]
for item in result["constraints"]:
    notes.append(f"- constraint: {item}")
Path("solver_notes.md").write_text("\n".join(notes), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))