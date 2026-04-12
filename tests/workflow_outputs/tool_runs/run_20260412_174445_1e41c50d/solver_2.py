from __future__ import annotations
import json
import re
from pathlib import Path

context = {
  "problem_text": "问题1：请预测未来 7 天销量，并说明误差评估方法。\n问题2：在预算约束下最大化利润，并给出敏感性分析建议。",
  "clarifications": [
    "Which variables are the decision variables, state variables, and outputs?",
    "Which constraints must always hold?",
    "Which claims require quantitative evidence before they can appear in the final paper?"
  ],
  "subproblem_index": 2,
  "subproblem": {
    "title": "问题2",
    "text": "在预算约束下最大化利润，并给出敏感性分析建议。",
    "analysis": {
      "task_types": [
        "优化/决策"
      ],
      "candidate_models": [
        "线性规划",
        "整数规划/混合整数规划",
        "多目标优化"
      ],
      "solution_plan": [
        "先明确输入、输出、约束和评价指标，避免模型目标漂移。",
        "把文字规则转成决策变量、目标函数和约束条件。",
        "区分连续变量、整数变量和 0-1 变量。",
        "求解后做可行性检查和敏感性分析。"
      ],
      "key_variables": [
        "决策变量",
        "目标函数值",
        "约束边界"
      ],
      "needed_data": [
        "成本、收益或资源参数",
        "业务约束与上限"
      ],
      "evaluation": [
        "检查假设是否合理、变量定义是否一致。",
        "检查解的可行性和边界情况。",
        "做敏感性分析。"
      ],
      "notes": [
        "先把题目里的变量、单位、边界条件统一。",
        "避免在没有数据支撑时直接给出数值结论。"
      ],
      "objective": "在满足约束的前提下最大化收益、效率或覆盖率。",
      "constraints": [
        "题目文本中存在显式约束，需要转写为数学不等式或逻辑条件。",
        "需要明确资源上限、容量约束和业务规则。"
      ],
      "assumptions": [
        "变量定义清晰且可以被观测、估计或求解。",
        "原始题面没有说明的外部环境在分析周期内保持相对稳定。",
        "成本、收益或资源参数在求解区间内可视为已知。"
      ],
      "deliverables": [
        "结构化建模思路",
        "关键公式或算法流程",
        "可复核的结论说明",
        "最优方案与敏感性分析"
      ],
      "formulation_steps": [
        "目标定义：在满足约束的前提下最大化收益、效率或覆盖率。",
        "约束梳理：题目文本中存在显式约束，需要转写为数学不等式或逻辑条件。",
        "把目标与约束写成线性规划、整数规划或多目标优化模型。"
      ],
      "chosen_method": "线性规划",
      "confidence": 0.75
    }
  },
  "all_subproblems": [
    {
      "title": "问题1",
      "text": "请预测未来 7 天销量，并说明误差评估方法。",
      "analysis": {
        "task_types": [
          "预测/拟合"
        ],
        "candidate_models": [
          "线性/非线性回归",
          "ARIMA/Prophet",
          "灰色预测 GM(1,1)"
        ],
        "solution_plan": [
          "先明确输入、输出、约束和评价指标，避免模型目标漂移。",
          "整理历史数据并检查缺失、异常值和单位一致性。",
          "先建立基线模型，再与更复杂模型做对比。",
          "使用误差指标和回测结果评估预测稳定性。"
        ],
        "key_variables": [
          "时间索引",
          "目标变量",
          "解释变量"
        ],
        "needed_data": [
          "历史观测数据",
          "外部影响因素或特征变量"
        ],
        "evaluation": [
          "检查假设是否合理、变量定义是否一致。",
          "使用 MAE、RMSE、MAPE 等误差指标。",
          "进行回测或验证集评估。"
        ],
        "notes": [
          "先把题目里的变量、单位、边界条件统一。",
          "避免在没有数据支撑时直接给出数值结论。"
        ],
        "objective": "建立预测模型并给出可解释的误差评估。",
        "constraints": [
          "训练与验证数据划分方式需要保持时序一致。"
        ],
        "assumptions": [
          "变量定义清晰且可以被观测、估计或求解。",
          "原始题面没有说明的外部环境在分析周期内保持相对稳定。",
          "历史数据对未来具有一定代表性。"
        ],
        "deliverables": [
          "结构化建模思路",
          "关键公式或算法流程",
          "可复核的结论说明",
          "预测结果与误差分析"
        ],
        "formulation_steps": [
          "目标定义：建立预测模型并给出可解释的误差评估。",
          "约束梳理：训练与验证数据划分方式需要保持时序一致。",
          "构建特征和时间索引，给出训练、验证和预测流程。"
        ],
        "chosen_method": "线性/非线性回归",
        "confidence": 0.75
      }
    },
    {
      "title": "问题2",
      "text": "在预算约束下最大化利润，并给出敏感性分析建议。",
      "analysis": {
        "task_types": [
          "优化/决策"
        ],
        "candidate_models": [
          "线性规划",
          "整数规划/混合整数规划",
          "多目标优化"
        ],
        "solution_plan": [
          "先明确输入、输出、约束和评价指标，避免模型目标漂移。",
          "把文字规则转成决策变量、目标函数和约束条件。",
          "区分连续变量、整数变量和 0-1 变量。",
          "求解后做可行性检查和敏感性分析。"
        ],
        "key_variables": [
          "决策变量",
          "目标函数值",
          "约束边界"
        ],
        "needed_data": [
          "成本、收益或资源参数",
          "业务约束与上限"
        ],
        "evaluation": [
          "检查假设是否合理、变量定义是否一致。",
          "检查解的可行性和边界情况。",
          "做敏感性分析。"
        ],
        "notes": [
          "先把题目里的变量、单位、边界条件统一。",
          "避免在没有数据支撑时直接给出数值结论。"
        ],
        "objective": "在满足约束的前提下最大化收益、效率或覆盖率。",
        "constraints": [
          "题目文本中存在显式约束，需要转写为数学不等式或逻辑条件。",
          "需要明确资源上限、容量约束和业务规则。"
        ],
        "assumptions": [
          "变量定义清晰且可以被观测、估计或求解。",
          "原始题面没有说明的外部环境在分析周期内保持相对稳定。",
          "成本、收益或资源参数在求解区间内可视为已知。"
        ],
        "deliverables": [
          "结构化建模思路",
          "关键公式或算法流程",
          "可复核的结论说明",
          "最优方案与敏感性分析"
        ],
        "formulation_steps": [
          "目标定义：在满足约束的前提下最大化收益、效率或覆盖率。",
          "约束梳理：题目文本中存在显式约束，需要转写为数学不等式或逻辑条件。",
          "把目标与约束写成线性规划、整数规划或多目标优化模型。"
        ],
        "chosen_method": "线性规划",
        "confidence": 0.75
      }
    }
  ],
  "model": {
    "assumptions": [
      "变量定义清晰且可以被观测、估计或求解。",
      "原始题面没有说明的外部环境在分析周期内保持相对稳定。",
      "历史数据对未来具有一定代表性。",
      "成本、收益或资源参数在求解区间内可视为已知。"
    ],
    "constraints": [
      "训练与验证数据划分方式需要保持时序一致。",
      "题目文本中存在显式约束，需要转写为数学不等式或逻辑条件。",
      "需要明确资源上限、容量约束和业务规则。"
    ],
    "method_candidates": [
      "线性/非线性回归",
      "ARIMA/Prophet",
      "灰色预测 GM(1,1)",
      "线性规划",
      "整数规划/混合整数规划",
      "多目标优化"
    ],
    "chosen_method": "线性/非线性回归",
    "formulation_outline": [
      "目标定义：建立预测模型并给出可解释的误差评估。",
      "约束梳理：训练与验证数据划分方式需要保持时序一致。",
      "构建特征和时间索引，给出训练、验证和预测流程。",
      "目标定义：在满足约束的前提下最大化收益、效率或覆盖率。",
      "约束梳理：题目文本中存在显式约束，需要转写为数学不等式或逻辑条件。",
      "把目标与约束写成线性规划、整数规划或多目标优化模型。"
    ],
    "evidence_gaps": [
      "历史观测数据",
      "外部影响因素或特征变量",
      "成本、收益或资源参数",
      "业务约束与上限"
    ]
  }
}
subproblem = context["subproblem"]
analysis = subproblem["analysis"]
text = subproblem["text"] or context["problem_text"]
numbers = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]
budget = max(numbers) if numbers else 0.0
candidate_costs = sorted(x for x in numbers if x > 0)
chosen_cost = candidate_costs[0] if candidate_costs else 0.0
remaining_budget = budget - chosen_cost if budget else 0.0
status = "ok" if candidate_costs and budget else "partial"
result = {
    "subproblem_title": subproblem["title"],
    "status": status,
    "method": analysis.get("chosen_method") or "baseline_optimization_template",
    "objective": analysis.get("objective") or "Produce a baseline feasible decision summary from detected parameters.",
    "assumptions": analysis.get("assumptions") or ["The largest detected number is treated as a rough budget upper bound."],
    "constraints": analysis.get("constraints") or ["A formal mathematical program still needs explicit decision variables and constraints."],
    "result_summary": (
        "Generated a baseline feasible decision note using detected positive numbers as candidate costs."
    ),
    "evidence": [
        "template_used=baseline_optimization_template",
        f"budget={budget}",
        f"candidate_cost_count={len(candidate_costs)}",
        f"chosen_cost={chosen_cost}",
    ],
    "numeric_results": {
        "budget": round(budget, 4),
        "candidate_cost_count": len(candidate_costs),
        "chosen_cost": round(chosen_cost, 4),
        "remaining_budget": round(remaining_budget, 4),
    },
    "artifacts": ["result.json", "optimization_summary.json"],
    "next_steps": [
        "Translate the subproblem into decision variables, objective, and constraints.",
        "Use a proper LP/MIP solver when tabular data becomes available.",
    ],
}
Path("result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
Path("optimization_summary.json").write_text(
    json.dumps(
        {
            "candidate_costs": candidate_costs[:20],
            "budget": budget,
            "chosen_cost": chosen_cost,
            "remaining_budget": remaining_budget,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps(result, ensure_ascii=False))