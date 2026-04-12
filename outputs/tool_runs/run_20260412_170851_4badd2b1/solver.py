from __future__ import annotations
import json
import re
from pathlib import Path

context = {
  "problem_text": "你好",
  "clarifications": [
    "问题 的硬约束和软约束分别是什么？"
  ],
  "subproblems": [
    {
      "title": "问题",
      "text": "你好",
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
problem_text = context["problem_text"]
numbers = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", problem_text)]
summary = {
    "subproblem_count": len(context["subproblems"]),
    "subproblem_titles": [item["title"] for item in context["subproblems"]],
    "recommended_methods": [
        item["analysis"].get("chosen_method") or "待确认"
        for item in context["subproblems"]
    ],
    "detected_numbers": numbers[:20],
}
Path("solver_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
lines = [
    "# Solver Notes",
    "",
    f"- subproblem_count: {summary['subproblem_count']}",
    f"- detected_numbers: {summary['detected_numbers']}",
]
for item in context["subproblems"]:
    analysis = item["analysis"]
    lines.extend(
        [
            "",
            f"## {item['title']}",
            f"- objective: {analysis.get('objective') or '待确认'}",
            f"- chosen_method: {analysis.get('chosen_method') or '待确认'}",
            "- constraints:",
        ]
    )
    constraints = analysis.get("constraints") or ["待补充"]
    for constraint in constraints:
        lines.append(f"  - {constraint}")
Path("solver_notes.md").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))