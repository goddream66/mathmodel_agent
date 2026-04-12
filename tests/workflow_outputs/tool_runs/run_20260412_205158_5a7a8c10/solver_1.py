from __future__ import annotations
import json
import re
import statistics
from pathlib import Path

context = {
  "problem_text": "问题1：请预测未来 7 天销量，并说明误差评估方法。\n问题2：在预算约束下最大化利润，并给出敏感性分析建议。",
  "clarifications": [
    "Which variables are the decision variables, state variables, and outputs?",
    "Which constraints must always hold?",
    "Which claims require quantitative evidence before they can appear in the final paper?"
  ],
  "subproblem_index": 1,
  "subproblem": {
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
tables = [table for table in context.get("input_data", {}).get("tables", []) if table.get("kind") == "table"]
text = subproblem["text"] or context["problem_text"]
numbers = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]
horizon_match = re.search(r"(?:next|future|ahead|未来|接下来)\s*(\d+)", text, re.IGNORECASE)
forecast_horizon = int(horizon_match.group(1)) if horizon_match else 1
def _numeric_columns(table):
    columns = []
    for column in table.get("columns", []):
        values = [row.get(column) for row in table.get("rows", [])]
        numeric_values = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if numeric_values:
            columns.append(column)
    return columns

def _choose_series_from_tables():
    for table in tables:
        numeric_columns = _numeric_columns(table)
        if not numeric_columns:
            continue
        task_roles = table.get("task_roles", {}).get("forecast", {})
        selected = task_roles.get("value") or table.get("column_roles", {}).get("value")
        if selected is None:
            preferred = ["value", "values", "demand", "sales", "quantity", "target", "y"]
            lower_map = {col.lower(): col for col in numeric_columns}
            for name in preferred:
                if name in lower_map:
                    selected = lower_map[name]
                    break
        if selected is None or selected not in numeric_columns:
            selected = numeric_columns[-1]
        series_values = [
            float(row[selected])
            for row in table.get("rows", [])
            if isinstance(row.get(selected), (int, float)) and not isinstance(row.get(selected), bool)
        ]
        if len(series_values) >= 2:
            return table.get("name", "table"), selected, series_values
    return None, None, []

table_name, selected_column, series = _choose_series_from_tables()
if not series:
    series = list(numbers)
if horizon_match:
    horizon_value = float(forecast_horizon)
    removed = False
    filtered = []
    for value in series:
        if not removed and value == horizon_value:
            removed = True
            continue
        filtered.append(value)
    series = filtered
library_used = "stdlib"
try:
    import numpy as np
except Exception:
    np = None
try:
    import pandas as pd
except Exception:
    pd = None

if len(series) >= 2 and np is not None:
    arr = np.array(series, dtype=float)
    avg = float(arr.mean())
    trend = float(np.polyfit(np.arange(len(arr)), arr, 1)[0])
    forecast_value = float(arr[-1] + trend)
    status = "ok"
    library_used = "numpy"
elif len(series) >= 2:
    avg = float(statistics.fmean(series))
    deltas = [series[i] - series[i - 1] for i in range(1, len(series))]
    trend = float(statistics.fmean(deltas))
    forecast_value = float(series[-1] + trend)
    status = "ok"
else:
    avg = float(series[0]) if series else 0.0
    trend = 0.0
    forecast_value = avg
    status = "partial"

rolling_mean = avg
if series and pd is not None:
    rolling_mean = float(pd.Series(series, dtype="float64").rolling(min(3, len(series))).mean().iloc[-1])
    if library_used == "stdlib":
        library_used = "pandas"

result = {
    "subproblem_title": subproblem["title"],
    "status": status,
    "method": analysis.get("chosen_method") or "forecast_template_solver",
    "objective": analysis.get("objective") or "Estimate a baseline forecast from available numeric clues.",
    "assumptions": analysis.get("assumptions") or ["Observed values are representative for a baseline extrapolation."],
    "constraints": analysis.get("constraints") or ["Formal training data is unavailable in the current context."],
    "result_summary": f"Built a baseline forecast for horizon={forecast_horizon} using {len(series)} historical points with {library_used}.",
    "evidence": [
        "template_used=baseline_forecast_template",
        f"library_used={library_used}",
        f"table_name={table_name or 'none'}",
        f"selected_column={selected_column or 'none'}",
        f"historical_point_count={len(series)}",
        f"average_value={avg}",
        f"average_delta={trend}",
    ],
    "numeric_results": {
        "forecast_horizon": forecast_horizon,
        "historical_point_count": len(series),
        "baseline_average": round(avg, 4),
        "rolling_mean": round(rolling_mean, 4),
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