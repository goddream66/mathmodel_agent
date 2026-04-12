from __future__ import annotations
import json
import re
from pathlib import Path

context = {
  "problem_text": "Problem 1: forecast demand for the next 5 days using values 10 12 15 18 20.\nProblem 2: optimize cost under budget 100 with candidate costs 25 40 70.\nProblem 3: find a path with distances 9 4 7 3.\nProblem 4: evaluate alternatives with scores 80 76 91.",
  "clarifications": [
    "Problem 4: what are the hard and soft constraints?"
  ],
  "subproblem_index": 4,
  "subproblem": {
    "title": "Problem 4",
    "text": "evaluate alternatives with scores 80 76 91.",
    "analysis": {
      "task_types": [
        "评价/权重"
      ],
      "candidate_models": [
        "AHP",
        "熵权法",
        "TOPSIS"
      ],
      "solution_plan": [
        "先明确输入、输出、约束和评价指标，避免模型目标漂移。",
        "建立指标体系并标明正向、逆向指标。",
        "选择 AHP、熵权或 TOPSIS 形成综合评价。",
        "检查权重稳定性和排序鲁棒性。"
      ],
      "key_variables": [
        "指标值",
        "指标权重",
        "综合得分"
      ],
      "needed_data": [
        "指标明细数据",
        "指标方向说明"
      ],
      "evaluation": [
        "检查假设是否合理、变量定义是否一致。",
        "检查排序稳定性和权重鲁棒性。"
      ],
      "notes": [
        "先把题目里的变量、单位、边界条件统一。",
        "避免在没有数据支撑时直接给出数值结论。"
      ],
      "objective": "构建评价体系并形成可信的排序结果。",
      "constraints": [],
      "assumptions": [
        "变量定义清晰且可以被观测、估计或求解。",
        "原始题面没有说明的外部环境在分析周期内保持相对稳定。"
      ],
      "deliverables": [
        "结构化建模思路",
        "关键公式或算法流程",
        "可复核的结论说明",
        "评价排序与权重解释"
      ],
      "formulation_steps": [
        "目标定义：构建评价体系并形成可信的排序结果。",
        "先标准化指标，再进行赋权与综合评分。"
      ],
      "chosen_method": "AHP",
      "confidence": 0.75
    }
  },
  "all_subproblems": [
    {
      "title": "Problem 1",
      "text": "forecast demand for the next 5 days using values 10 12 15 18 20.",
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
      "text": "optimize cost under budget 100 with candidate costs 25 40 70.",
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
    {
      "title": "Problem 3",
      "text": "find a path with distances 9 4 7 3.",
      "analysis": {
        "task_types": [
          "路径/网络"
        ],
        "candidate_models": [
          "最短路径模型",
          "最小费用流",
          "车辆路径问题"
        ],
        "solution_plan": [
          "先明确输入、输出、约束和评价指标，避免模型目标漂移。",
          "先抽象成图结构，明确节点、边和权重。",
          "根据目标选择最短路、最小费用流或车辆路径模型。",
          "验证容量、时间窗和路径连通性等业务约束。"
        ],
        "key_variables": [
          "节点集合",
          "边权重",
          "路径选择变量"
        ],
        "needed_data": [
          "节点和边信息",
          "距离、时间或费用矩阵"
        ],
        "evaluation": [
          "检查假设是否合理、变量定义是否一致。",
          "比较总路径长度、总成本或准时率。"
        ],
        "notes": [
          "先把题目里的变量、单位、边界条件统一。",
          "避免在没有数据支撑时直接给出数值结论。"
        ],
        "objective": "在网络结构约束下找到最优路径或调度方案。",
        "constraints": [
          "需要验证连通性、容量或时间窗约束。"
        ],
        "assumptions": [
          "变量定义清晰且可以被观测、估计或求解。",
          "原始题面没有说明的外部环境在分析周期内保持相对稳定。"
        ],
        "deliverables": [
          "结构化建模思路",
          "关键公式或算法流程",
          "可复核的结论说明",
          "路径或调度方案"
        ],
        "formulation_steps": [
          "目标定义：在网络结构约束下找到最优路径或调度方案。",
          "约束梳理：需要验证连通性、容量或时间窗约束。",
          "把问题映射到图模型并定义节点、边和权重。"
        ],
        "chosen_method": "最短路径模型",
        "confidence": 0.75
      }
    },
    {
      "title": "Problem 4",
      "text": "evaluate alternatives with scores 80 76 91.",
      "analysis": {
        "task_types": [
          "评价/权重"
        ],
        "candidate_models": [
          "AHP",
          "熵权法",
          "TOPSIS"
        ],
        "solution_plan": [
          "先明确输入、输出、约束和评价指标，避免模型目标漂移。",
          "建立指标体系并标明正向、逆向指标。",
          "选择 AHP、熵权或 TOPSIS 形成综合评价。",
          "检查权重稳定性和排序鲁棒性。"
        ],
        "key_variables": [
          "指标值",
          "指标权重",
          "综合得分"
        ],
        "needed_data": [
          "指标明细数据",
          "指标方向说明"
        ],
        "evaluation": [
          "检查假设是否合理、变量定义是否一致。",
          "检查排序稳定性和权重鲁棒性。"
        ],
        "notes": [
          "先把题目里的变量、单位、边界条件统一。",
          "避免在没有数据支撑时直接给出数值结论。"
        ],
        "objective": "构建评价体系并形成可信的排序结果。",
        "constraints": [],
        "assumptions": [
          "变量定义清晰且可以被观测、估计或求解。",
          "原始题面没有说明的外部环境在分析周期内保持相对稳定。"
        ],
        "deliverables": [
          "结构化建模思路",
          "关键公式或算法流程",
          "可复核的结论说明",
          "评价排序与权重解释"
        ],
        "formulation_steps": [
          "目标定义：构建评价体系并形成可信的排序结果。",
          "先标准化指标，再进行赋权与综合评分。"
        ],
        "chosen_method": "AHP",
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
      "需要明确资源上限、容量约束和业务规则。",
      "需要验证连通性、容量或时间窗约束。"
    ],
    "method_candidates": [
      "线性/非线性回归",
      "ARIMA/Prophet",
      "灰色预测 GM(1,1)",
      "线性规划",
      "整数规划/混合整数规划",
      "多目标优化",
      "最短路径模型",
      "最小费用流"
    ],
    "chosen_method": "线性/非线性回归",
    "formulation_outline": [
      "目标定义：建立预测模型并给出可解释的误差评估。",
      "约束梳理：训练与验证数据划分方式需要保持时序一致。",
      "构建特征和时间索引，给出训练、验证和预测流程。",
      "目标定义：构建目标函数并求得最优决策方案。",
      "约束梳理：需要明确资源上限、容量约束和业务规则。",
      "把目标与约束写成线性规划、整数规划或多目标优化模型。",
      "目标定义：在网络结构约束下找到最优路径或调度方案。",
      "约束梳理：需要验证连通性、容量或时间窗约束。",
      "把问题映射到图模型并定义节点、边和权重。",
      "目标定义：构建评价体系并形成可信的排序结果。"
    ],
    "evidence_gaps": [
      "历史观测数据",
      "外部影响因素或特征变量",
      "成本、收益或资源参数",
      "业务约束与上限",
      "节点和边信息",
      "距离、时间或费用矩阵",
      "指标明细数据",
      "指标方向说明"
    ]
  }
}
subproblem = context["subproblem"]
analysis = subproblem["analysis"]
tables = [table for table in context.get("input_data", {}).get("tables", []) if table.get("kind") == "table"]
text = subproblem["text"] or context["problem_text"]
numbers = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]
indicator_count = len(analysis.get("key_variables") or [])
library_used = "stdlib"
table_name = None
score_columns = []
weighted_scores = []
for table in tables:
    numeric_columns = []
    for column in table.get("columns", []):
        values = [row.get(column) for row in table.get("rows", [])]
        if any(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
            numeric_columns.append(column)
    if numeric_columns:
        table_name = table.get("name", "table")
        task_roles = table.get("task_roles", {}).get("evaluation", {})
        weight_column = task_roles.get("weight") or table.get("column_roles", {}).get("weight")
        if weight_column is None:
            lower_map = {str(column).lower(): str(column) for column in numeric_columns}
            weight_column = lower_map.get("weight") or lower_map.get("weights")
        score_columns = [column for column in numeric_columns if str(column) != str(weight_column)]
        if score_columns:
            for row in table.get("rows", []):
                values = [float(row[column]) for column in score_columns if isinstance(row.get(column), (int, float))]
                if not values:
                    continue
                base_score = sum(values) / len(values)
                if weight_column and isinstance(row.get(weight_column), (int, float)):
                    base_score *= float(row[weight_column])
                weighted_scores.append(float(base_score))
            if weighted_scores:
                numbers = weighted_scores
                indicator_count = len(score_columns)
                break
if numbers:
    try:
        import numpy as np
    except Exception:
        np = None
    try:
        from scipy.stats import rankdata
    except Exception:
        rankdata = None
    if np is not None:
        arr = np.array(numbers, dtype=float)
        average_score = float(arr.mean())
        max_score = float(arr.max())
        normalized = (arr / arr.sum()).tolist() if float(arr.sum()) else arr.tolist()
        library_used = "numpy"
    else:
        average_score = float(sum(numbers) / len(numbers))
        max_score = float(max(numbers))
        total = float(sum(numbers))
        normalized = [float(x / total) if total else 0.0 for x in numbers]
    if rankdata is not None:
        best_rank = int(rankdata([-x for x in numbers], method="dense")[0])
        if library_used == "stdlib":
            library_used = "scipy"
    else:
        best_rank = 1
else:
    average_score = 0.0
    max_score = 0.0
    normalized = []
    best_rank = 0
status = "ok" if numbers else "partial"
result = {
    "subproblem_title": subproblem["title"],
    "status": status,
    "method": analysis.get("chosen_method") or "evaluation_template_solver",
    "objective": analysis.get("objective") or "Produce a baseline evaluation summary.",
    "assumptions": analysis.get("assumptions") or ["Detected numbers are treated as rough indicator values."],
    "constraints": analysis.get("constraints") or ["Formal indicator definitions and weights still need confirmation."],
    "result_summary": f"Generated a baseline evaluation summary using {library_used}.",
    "evidence": [
        "template_used=baseline_evaluation_template",
        f"library_used={library_used}",
        f"table_name={table_name or 'none'}",
        f"score_column_count={len(score_columns)}",
        f"indicator_count={indicator_count}",
        f"number_count={len(numbers)}",
        f"average_score={average_score}",
    ],
    "numeric_results": {
        "indicator_count": indicator_count,
        "number_count": len(numbers),
        "average_score": round(average_score, 4),
        "max_score": round(max_score, 4),
        "best_rank": best_rank,
    },
    "artifacts": ["result.json", "evaluation_summary.json"],
    "next_steps": [
        "Add explicit indicator definitions and directions before formal ranking.",
        "Use AHP, entropy weighting, or TOPSIS once a complete indicator table is available.",
    ],
}
Path("result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
Path("evaluation_summary.json").write_text(
    json.dumps(
        {
            "numbers": numbers[:20],
            "average_score": average_score,
            "max_score": max_score,
            "normalized_scores": normalized[:20],
            "best_rank": best_rank,
            "indicator_count": indicator_count,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps(result, ensure_ascii=False))