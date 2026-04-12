from __future__ import annotations
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
  "subproblem_index": 1,
  "subproblem": {
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
text = subproblem["text"] or context["problem_text"]
numbers = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]
forecast_horizon = int(numbers[0]) if numbers else 1
series = numbers[1:] if len(numbers) > 1 else []
if len(series) >= 2:
    avg = sum(series) / len(series)
    deltas = [series[i] - series[i - 1] for i in range(1, len(series))]
    trend = sum(deltas) / len(deltas)
    forecast_value = avg + trend
    status = "ok"
else:
    avg = series[0] if series else 0.0
    trend = 0.0
    forecast_value = avg
    status = "partial"
result = {
    "subproblem_title": subproblem["title"],
    "status": status,
    "method": analysis.get("chosen_method") or "baseline_forecast_template",
    "objective": analysis.get("objective") or "Estimate a baseline forecast from available numeric clues.",
    "assumptions": analysis.get("assumptions") or ["Observed values are representative for a baseline extrapolation."],
    "constraints": analysis.get("constraints") or ["Formal training data is unavailable in the current context."],
    "result_summary": f"Built a simple baseline forecast for horizon={forecast_horizon} using {len(series)} historical points.",
    "evidence": [
        f"historical_point_count={len(series)}",
        f"average_value={avg}",
        f"average_delta={trend}",
    ],
    "numeric_results": {
        "forecast_horizon": forecast_horizon,
        "historical_point_count": len(series),
        "baseline_average": round(avg, 4),
        "baseline_trend": round(trend, 4),
        "forecast_value": round(forecast_value, 4),
    },
    "artifacts": ["result.json", "forecast_metrics.json"],
    "next_steps": [
        "Replace the baseline extrapolation with a time-series model if full data is available.",
        "Validate the forecast with MAE, RMSE, or MAPE once a hold-out set is available.",
    ],
}
Path("result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
Path("forecast_metrics.json").write_text(
    json.dumps(
        {
            "series": series,
            "baseline_average": avg,
            "baseline_trend": trend,
            "forecast_value": forecast_value,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps(result, ensure_ascii=False))