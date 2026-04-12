from __future__ import annotations
import itertools
import json
import re
from pathlib import Path

context = {
  "problem_text": "Problem 1: forecast demand for the next 7 days and report one numeric indicator.\nProblem 2: optimize cost under a budget of 100 and explain the chosen method.",
  "clarifications": [
    "Which variables are the decision variables, state variables, and outputs?",
    "Which constraints must always hold?",
    "Which claims require quantitative evidence before they can appear in the final paper?"
  ],
  "subproblem_index": 2,
  "subproblem": {
    "title": "Problem 2",
    "text": "optimize cost under a budget of 100 and explain the chosen method.",
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
      "objective": "构建目标函数并求得最优决策方案。",
      "constraints": [
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
        "目标定义：构建目标函数并求得最优决策方案。",
        "约束梳理：需要明确资源上限、容量约束和业务规则。",
        "把目标与约束写成线性规划、整数规划或多目标优化模型。"
      ],
      "chosen_method": "线性规划",
      "confidence": 0.75
    }
  },
  "all_subproblems": [
    {
      "title": "Problem 1",
      "text": "forecast demand for the next 7 days and report one numeric indicator.",
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
      "title": "Problem 2",
      "text": "optimize cost under a budget of 100 and explain the chosen method.",
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
        "objective": "构建目标函数并求得最优决策方案。",
        "constraints": [
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
          "目标定义：构建目标函数并求得最优决策方案。",
          "约束梳理：需要明确资源上限、容量约束和业务规则。",
          "把目标与约束写成线性规划、整数规划或多目标优化模型。"
        ],
        "chosen_method": "线性规划",
        "confidence": 0.75
      }
    }
  ],
  "input_data": {},
  "model": {
    "assumptions": [
      "变量定义清晰且可以被观测、估计或求解。",
      "原始题面没有说明的外部环境在分析周期内保持相对稳定。",
      "历史数据对未来具有一定代表性。",
      "成本、收益或资源参数在求解区间内可视为已知。"
    ],
    "constraints": [
      "训练与验证数据划分方式需要保持时序一致。",
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
      "目标定义：构建目标函数并求得最优决策方案。",
      "约束梳理：需要明确资源上限、容量约束和业务规则。",
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
tables = [table for table in context.get("input_data", {}).get("tables", []) if table.get("kind") == "table"]
text = subproblem["text"] or context["problem_text"]
numbers = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]
budget = max(numbers) if numbers else 0.0
def _pick_column(table, keywords):
    for column in table.get("columns", []):
        lower = str(column).lower()
        if any(keyword in lower for keyword in keywords):
            return column
    return None

candidate_costs = [x for x in numbers if x > 0]
candidate_values = list(candidate_costs)
table_name = None
cost_column = None
value_column = None
for table in tables:
    task_roles = table.get("task_roles", {}).get("optimization", {})
    cost_column = task_roles.get("cost") or table.get("column_roles", {}).get("cost")
    value_column = task_roles.get("value") or table.get("column_roles", {}).get("profit")
    if cost_column is None:
        cost_column = _pick_column(table, ["cost", "price", "expense", "weight", "budget"])
    if value_column is None:
        value_column = _pick_column(table, ["value", "profit", "revenue", "score", "benefit"])
    if cost_column:
        raw_costs = [
            float(row[cost_column])
            for row in table.get("rows", [])
            if isinstance(row.get(cost_column), (int, float)) and not isinstance(row.get(cost_column), bool)
        ]
        if raw_costs:
            candidate_costs = raw_costs
            if value_column:
                candidate_values = [
                    float(row[value_column])
                    for row in table.get("rows", [])
                    if isinstance(row.get(value_column), (int, float)) and not isinstance(row.get(value_column), bool)
                ]
                if len(candidate_values) != len(candidate_costs):
                    candidate_values = list(candidate_costs)
            else:
                candidate_values = list(candidate_costs)
            table_name = table.get("name", "table")
            break

if budget in candidate_costs and len(candidate_costs) > 1:
    candidate_costs.remove(budget)
candidate_costs = sorted(candidate_costs)
if len(candidate_values) != len(candidate_costs):
    candidate_values = list(candidate_costs)
library_used = "stdlib"
selected_costs = []
selected_value = 0.0
chosen_cost = 0.0
remaining_budget = budget
if candidate_costs and budget:
    try:
        import pulp
    except Exception:
        pulp = None
    if pulp is not None:
        problem = pulp.LpProblem("budget_select", pulp.LpMaximize)
        variables = [pulp.LpVariable(f"x_{i}", cat="Binary") for i in range(len(candidate_costs))]
        problem += pulp.lpSum(candidate_values[i] * variables[i] for i in range(len(candidate_costs)))
        problem += pulp.lpSum(candidate_costs[i] * variables[i] for i in range(len(candidate_costs))) <= budget
        problem.solve(pulp.PULP_CBC_CMD(msg=False))
        selected_costs = [
            candidate_costs[i]
            for i in range(len(candidate_costs))
            if variables[i].value() and variables[i].value() > 0.5
        ]
        selected_value = float(
            sum(candidate_values[i] for i in range(len(candidate_costs)) if variables[i].value() and variables[i].value() > 0.5)
        )
        chosen_cost = float(sum(selected_costs))
        remaining_budget = float(budget - chosen_cost)
        library_used = "pulp"
    else:
        best_subset = []
        best_sum = 0.0
        best_value = 0.0
        for r in range(1, len(candidate_costs) + 1):
            for combo_indices in itertools.combinations(range(len(candidate_costs)), r):
                total = float(sum(candidate_costs[i] for i in combo_indices))
                total_value = float(sum(candidate_values[i] for i in combo_indices))
                if total <= budget and (total_value > best_value or (total_value == best_value and total > best_sum)):
                    best_sum = total
                    best_value = total_value
                    best_subset = [candidate_costs[i] for i in combo_indices]
        selected_costs = best_subset
        chosen_cost = float(best_sum)
        selected_value = float(best_value)
        remaining_budget = float(budget - chosen_cost)
status = "ok" if candidate_costs and budget else "partial"
result = {
    "subproblem_title": subproblem["title"],
    "status": status,
    "method": analysis.get("chosen_method") or "optimization_template_solver",
    "objective": analysis.get("objective") or "Produce a baseline feasible decision summary from detected parameters.",
    "assumptions": analysis.get("assumptions") or ["The largest detected number is treated as a rough budget upper bound."],
    "constraints": analysis.get("constraints") or ["A formal mathematical program still needs explicit decision variables and constraints."],
    "result_summary": (
        f"Generated a baseline feasible decision note using {library_used}."
    ),
    "evidence": [
        "template_used=baseline_optimization_template",
        f"library_used={library_used}",
        f"table_name={table_name or 'none'}",
        f"cost_column={cost_column or 'none'}",
        f"value_column={value_column or 'none'}",
        f"budget={budget}",
        f"candidate_cost_count={len(candidate_costs)}",
        f"chosen_cost={chosen_cost}",
    ],
    "numeric_results": {
        "budget": round(budget, 4),
        "candidate_cost_count": len(candidate_costs),
        "chosen_cost": round(chosen_cost, 4),
        "selected_value": round(selected_value, 4),
        "remaining_budget": round(remaining_budget, 4),
        "selected_item_count": len(selected_costs),
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
            "selected_costs": selected_costs[:20],
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