from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..llm import Message, build_llm
from ..llm.config import load_llm_config
from ..llm.utils import extract_first_json
from ..memory import MemoryStore
from ..prompts import render_prompt
from ..reporting import required_report_titles
from ..skills import (
    ClarifySkill,
    ModelSkill,
    ProblemDecomposeSkill,
    ReportSkill,
    SolveSkill,
    SubProblemAnalyzeSkill,
    ValidateSkill,
)
from ..state import ExperimentArtifact, SolverRun, SubProblem, TaskState
from ..tools import ToolRegistry


RESULT_STATUS_VALUES = {"ok", "partial", "failed"}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        clean = str(item).strip()
        if clean:
            items.append(clean)
    return items


def _subproblem_payload(subproblem: SubProblem) -> dict[str, Any]:
    return {
        "title": subproblem.title,
        "text": subproblem.text,
        "analysis": {
            "task_types": subproblem.analysis.task_types,
            "candidate_models": subproblem.analysis.candidate_models,
            "solution_plan": subproblem.analysis.solution_plan,
            "key_variables": subproblem.analysis.key_variables,
            "needed_data": subproblem.analysis.needed_data,
            "evaluation": subproblem.analysis.evaluation,
            "notes": subproblem.analysis.notes,
            "objective": subproblem.analysis.objective,
            "constraints": subproblem.analysis.constraints,
            "assumptions": subproblem.analysis.assumptions,
            "deliverables": subproblem.analysis.deliverables,
            "formulation_steps": subproblem.analysis.formulation_steps,
            "chosen_method": subproblem.analysis.chosen_method,
            "confidence": subproblem.analysis.confidence,
        },
    }


def _subproblems_payload(state: TaskState) -> list[dict[str, Any]]:
    return [_subproblem_payload(subproblem) for subproblem in state.subproblems]


def _solver_runs_payload(state: TaskState) -> list[dict[str, Any]]:
    return [
        {
            "subproblem_title": run.subproblem_title,
            "success": run.success,
            "summary": run.summary,
            "stdout": run.stdout,
            "stderr": run.stderr,
            "artifacts": run.artifacts,
            "schema_valid": run.schema_valid,
            "structured_result": run.structured_result,
        }
        for run in state.solver_runs
    ]


def _load_solver_artifacts(run_dir: str, artifact_names: list[str]) -> list[ExperimentArtifact]:
    base_path = Path(run_dir)
    artifacts: list[ExperimentArtifact] = []
    for artifact_name in artifact_names:
        artifact_path = base_path / artifact_name
        if not artifact_path.exists() or not artifact_path.is_file():
            continue
        suffix = artifact_path.suffix.lower()
        if suffix == ".json":
            try:
                payload = json.loads(artifact_path.read_text(encoding="utf-8"))
                kind = "json"
            except Exception:
                payload = artifact_path.read_text(encoding="utf-8", errors="replace")
                kind = "text"
        elif suffix == ".py":
            payload = artifact_path.read_text(encoding="utf-8", errors="replace")
            kind = "code"
        else:
            payload = artifact_path.read_text(encoding="utf-8", errors="replace")
            kind = "text"
        artifacts.append(ExperimentArtifact(name=artifact_name, kind=kind, payload=payload))
    return artifacts


def _build_solver_context(state: TaskState, subproblem: SubProblem, index: int) -> dict[str, Any]:
    return {
        "problem_text": state.problem_text,
        "clarifications": state.clarifications,
        "subproblem_index": index,
        "subproblem": _subproblem_payload(subproblem),
        "all_subproblems": _subproblems_payload(state),
        "input_data": state.input_data,
        "model": {
            "assumptions": state.model.assumptions,
            "constraints": state.model.constraints,
            "method_candidates": state.model.method_candidates,
            "chosen_method": state.model.chosen_method,
            "formulation_outline": state.model.formulation_outline,
            "evidence_gaps": state.model.evidence_gaps,
        },
    }


def _extract_code_block(text: str) -> str:
    match = re.search(r"```python\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def _normalize_numeric_results(value: Any) -> dict[str, float | int | str]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, float | int | str] = {}
    for key, raw in value.items():
        clean_key = str(key).strip()
        if not clean_key:
            continue
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            normalized[clean_key] = raw
        else:
            normalized[clean_key] = str(raw).strip()
    return normalized


def _validate_result_schema(payload: Any, expected_title: str) -> tuple[bool, dict[str, Any], str]:
    if not isinstance(payload, dict):
        return False, {}, "structured result is not a JSON object"

    normalized = {
        "subproblem_title": str(payload.get("subproblem_title") or "").strip(),
        "status": str(payload.get("status") or "").strip().lower(),
        "method": str(payload.get("method") or "").strip(),
        "objective": str(payload.get("objective") or "").strip(),
        "assumptions": _string_list(payload.get("assumptions")),
        "constraints": _string_list(payload.get("constraints")),
        "result_summary": str(payload.get("result_summary") or "").strip(),
        "evidence": _string_list(payload.get("evidence")),
        "numeric_results": _normalize_numeric_results(payload.get("numeric_results")),
        "artifacts": _string_list(payload.get("artifacts")),
        "next_steps": _string_list(payload.get("next_steps")),
    }

    if not normalized["subproblem_title"]:
        return False, normalized, "missing subproblem_title"
    if normalized["subproblem_title"] != expected_title:
        return False, normalized, "subproblem_title does not match current subproblem"
    if normalized["status"] not in RESULT_STATUS_VALUES:
        return False, normalized, "status must be one of ok/partial/failed"
    if not normalized["method"]:
        return False, normalized, "missing method"
    if not normalized["result_summary"]:
        return False, normalized, "missing result_summary"
    if not normalized["evidence"]:
        return False, normalized, "evidence must contain at least one item"
    return True, normalized, ""


def _extract_structured_result(run_dir: str, artifacts: list[str], stdout: str, expected_title: str) -> tuple[bool, dict[str, Any], str]:
    base_path = Path(run_dir)
    if "result.json" in artifacts:
        candidate = base_path / "result.json"
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception as exc:
            return False, {}, f"failed to parse result.json: {exc}"
        return _validate_result_schema(payload, expected_title)

    stdout_text = stdout.strip()
    if stdout_text:
        last_line = stdout_text.splitlines()[-1]
        try:
            payload = json.loads(last_line)
        except Exception:
            return False, {}, "missing result.json and stdout is not valid JSON"
        return _validate_result_schema(payload, expected_title)
    return False, {}, "missing result.json and empty stdout"


def _primary_task_type(context: dict[str, Any]) -> str:
    task_types = [
        str(item).strip()
        for item in context["subproblem"]["analysis"].get("task_types", [])
        if str(item).strip()
    ]
    priorities = [
        "预测/拟合",
        "优化/决策",
        "路径/网络",
        "评价/权重",
        "随机/仿真",
        "分类/判别",
        "聚类/分群",
        "参数估计",
        "通用建模",
    ]
    for name in priorities:
        if name in task_types:
            return name
    return task_types[0] if task_types else "通用建模"


def _build_forecast_solver_code(context: dict[str, Any]) -> tuple[str, str]:
    context_json = json.dumps(context, ensure_ascii=False, indent=2)
    title = context["subproblem"]["title"]
    summary = f"Forecast solver template generated a baseline result for {title}."
    code = f"""from __future__ import annotations
import json
import re
import statistics
from pathlib import Path

context = {context_json}
subproblem = context["subproblem"]
analysis = subproblem["analysis"]
tables = [table for table in context.get("input_data", {{}}).get("tables", []) if table.get("kind") == "table"]
text = subproblem["text"] or context["problem_text"]
numbers = [float(x) for x in re.findall(r"-?\\d+(?:\\.\\d+)?", text)]
horizon_match = re.search(r"(?:next|future|ahead|未来|接下来)\\s*(\\d+)", text, re.IGNORECASE)
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
        task_roles = table.get("task_roles", {{}}).get("forecast", {{}})
        selected = task_roles.get("value") or table.get("column_roles", {{}}).get("value")
        if selected is None:
            preferred = ["value", "values", "demand", "sales", "quantity", "target", "y"]
            lower_map = {{col.lower(): col for col in numeric_columns}}
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

result = {{
    "subproblem_title": subproblem["title"],
    "status": status,
    "method": analysis.get("chosen_method") or "forecast_template_solver",
    "objective": analysis.get("objective") or "Estimate a baseline forecast from available numeric clues.",
    "assumptions": analysis.get("assumptions") or ["Observed values are representative for a baseline extrapolation."],
    "constraints": analysis.get("constraints") or ["Formal training data is unavailable in the current context."],
    "result_summary": f"Built a baseline forecast for horizon={{forecast_horizon}} using {{len(series)}} historical points with {{library_used}}.",
    "evidence": [
        "template_used=baseline_forecast_template",
        f"library_used={{library_used}}",
        f"table_name={{table_name or 'none'}}",
        f"selected_column={{selected_column or 'none'}}",
        f"historical_point_count={{len(series)}}",
        f"average_value={{avg}}",
        f"average_delta={{trend}}",
    ],
    "numeric_results": {{
        "forecast_horizon": forecast_horizon,
        "historical_point_count": len(series),
        "baseline_average": round(avg, 4),
        "rolling_mean": round(rolling_mean, 4),
        "baseline_trend": round(trend, 4),
        "forecast_value": round(forecast_value, 4),
    }},
    "artifacts": ["result.json", "forecast_metrics.json"],
    "next_steps": [
        "Replace the baseline extrapolation with a time-series model if full data is available.",
        "Validate the forecast with MAE, RMSE, or MAPE once a hold-out set is available.",
    ],
}}
Path("result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
Path("forecast_metrics.json").write_text(
    json.dumps(
        {{
            "series": series,
            "baseline_average": avg,
            "baseline_trend": trend,
            "forecast_value": forecast_value,
        }},
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps(result, ensure_ascii=False))
"""
    return summary, code


def _build_optimization_solver_code(context: dict[str, Any]) -> tuple[str, str]:
    context_json = json.dumps(context, ensure_ascii=False, indent=2)
    title = context["subproblem"]["title"]
    summary = f"Optimization solver template generated a baseline result for {title}."
    code = f"""from __future__ import annotations
import itertools
import json
import re
from pathlib import Path

context = {context_json}
subproblem = context["subproblem"]
analysis = subproblem["analysis"]
tables = [table for table in context.get("input_data", {{}}).get("tables", []) if table.get("kind") == "table"]
text = subproblem["text"] or context["problem_text"]
numbers = [float(x) for x in re.findall(r"-?\\d+(?:\\.\\d+)?", text)]
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
    task_roles = table.get("task_roles", {{}}).get("optimization", {{}})
    cost_column = task_roles.get("cost") or table.get("column_roles", {{}}).get("cost")
    value_column = task_roles.get("value") or table.get("column_roles", {{}}).get("profit")
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
        variables = [pulp.LpVariable(f"x_{{i}}", cat="Binary") for i in range(len(candidate_costs))]
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
result = {{
    "subproblem_title": subproblem["title"],
    "status": status,
    "method": analysis.get("chosen_method") or "optimization_template_solver",
    "objective": analysis.get("objective") or "Produce a baseline feasible decision summary from detected parameters.",
    "assumptions": analysis.get("assumptions") or ["The largest detected number is treated as a rough budget upper bound."],
    "constraints": analysis.get("constraints") or ["A formal mathematical program still needs explicit decision variables and constraints."],
    "result_summary": (
        f"Generated a baseline feasible decision note using {{library_used}}."
    ),
    "evidence": [
        "template_used=baseline_optimization_template",
        f"library_used={{library_used}}",
        f"table_name={{table_name or 'none'}}",
        f"cost_column={{cost_column or 'none'}}",
        f"value_column={{value_column or 'none'}}",
        f"budget={{budget}}",
        f"candidate_cost_count={{len(candidate_costs)}}",
        f"chosen_cost={{chosen_cost}}",
    ],
    "numeric_results": {{
        "budget": round(budget, 4),
        "candidate_cost_count": len(candidate_costs),
        "chosen_cost": round(chosen_cost, 4),
        "selected_value": round(selected_value, 4),
        "remaining_budget": round(remaining_budget, 4),
        "selected_item_count": len(selected_costs),
    }},
    "artifacts": ["result.json", "optimization_summary.json"],
    "next_steps": [
        "Translate the subproblem into decision variables, objective, and constraints.",
        "Use a proper LP/MIP solver when tabular data becomes available.",
    ],
}}
Path("result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
Path("optimization_summary.json").write_text(
    json.dumps(
        {{
            "candidate_costs": candidate_costs[:20],
            "selected_costs": selected_costs[:20],
            "budget": budget,
            "chosen_cost": chosen_cost,
            "remaining_budget": remaining_budget,
        }},
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps(result, ensure_ascii=False))
"""
    return summary, code


def _build_path_solver_code(context: dict[str, Any]) -> tuple[str, str]:
    context_json = json.dumps(context, ensure_ascii=False, indent=2)
    title = context["subproblem"]["title"]
    summary = f"Path solver template generated a baseline result for {title}."
    code = f"""from __future__ import annotations
import json
import re
from pathlib import Path

context = {context_json}
subproblem = context["subproblem"]
analysis = subproblem["analysis"]
tables = [table for table in context.get("input_data", {{}}).get("tables", []) if table.get("kind") == "table"]
text = subproblem["text"] or context["problem_text"]
numbers = [float(x) for x in re.findall(r"-?\\d+(?:\\.\\d+)?", text)]
edge_count = max(len(numbers) - 1, 0)
library_used = "stdlib"
path_nodes = [f"N{{i}}" for i in range(len(numbers) + 1)] if numbers else []
table_name = None
source_column = None
target_column = None
weight_column = None
edge_rows = []
for table in tables:
    task_roles = table.get("task_roles", {{}}).get("path", {{}})
    source_column = task_roles.get("source") or table.get("column_roles", {{}}).get("source")
    target_column = task_roles.get("target") or table.get("column_roles", {{}}).get("target")
    weight_column = task_roles.get("weight") or table.get("column_roles", {{}}).get("weight")
    if not (source_column and target_column and weight_column):
        columns = list(table.get("columns", []))
        lower_map = {{str(column).lower(): str(column) for column in columns}}
        source_column = source_column or lower_map.get("source") or lower_map.get("from") or lower_map.get("start")
        target_column = target_column or lower_map.get("target") or lower_map.get("to") or lower_map.get("end")
        weight_column = weight_column or lower_map.get("weight") or lower_map.get("distance") or lower_map.get("cost")
    if source_column and target_column and weight_column:
        edge_rows = [
            row
            for row in table.get("rows", [])
            if row.get(source_column) not in {{None, ""}}
            and row.get(target_column) not in {{None, ""}}
            and isinstance(row.get(weight_column), (int, float))
            and not isinstance(row.get(weight_column), bool)
        ]
        if edge_rows:
            table_name = table.get("name", "table")
            break
if numbers:
    try:
        import networkx as nx
    except Exception:
        nx = None
    if nx is not None:
        graph = nx.Graph()
        if edge_rows:
            for row in edge_rows:
                graph.add_edge(str(row[source_column]), str(row[target_column]), weight=float(row[weight_column]))
            nodes = list(graph.nodes)
            start_node = nodes[0]
            end_node = nodes[-1]
            path_cost = float(nx.shortest_path_length(graph, start_node, end_node, weight="weight"))
            shortest_path = nx.shortest_path(graph, start_node, end_node, weight="weight")
            path_nodes = nodes
            edge_count = len(edge_rows)
        else:
            for i, weight in enumerate(numbers):
                graph.add_edge(path_nodes[i], path_nodes[i + 1], weight=float(weight))
            path_cost = float(nx.shortest_path_length(graph, path_nodes[0], path_nodes[-1], weight="weight"))
            shortest_path = nx.shortest_path(graph, path_nodes[0], path_nodes[-1], weight="weight")
        library_used = "networkx"
    else:
        if edge_rows:
            path_cost = float(sum(float(row[weight_column]) for row in edge_rows))
            shortest_path = [str(edge_rows[0][source_column])] + [str(row[target_column]) for row in edge_rows]
            path_nodes = _unique_path = []
            for node in shortest_path:
                if node not in _unique_path:
                    _unique_path.append(node)
            path_nodes = _unique_path
            edge_count = len(edge_rows)
        else:
            path_cost = float(sum(numbers))
            shortest_path = path_nodes
else:
    path_cost = 0.0
    shortest_path = []
status = "ok" if numbers else "partial"
result = {{
    "subproblem_title": subproblem["title"],
    "status": status,
    "method": analysis.get("chosen_method") or "path_template_solver",
    "objective": analysis.get("objective") or "Produce a baseline path summary from detected weights.",
    "assumptions": analysis.get("assumptions") or ["Detected numbers are treated as rough edge weights."],
    "constraints": analysis.get("constraints") or ["The full graph structure is not explicitly available in the prompt context."],
    "result_summary": f"Generated a baseline path/network summary using {{library_used}}.",
    "evidence": [
        "template_used=baseline_path_template",
        f"library_used={{library_used}}",
        f"table_name={{table_name or 'none'}}",
        f"source_column={{source_column or 'none'}}",
        f"target_column={{target_column or 'none'}}",
        f"weight_column={{weight_column or 'none'}}",
        f"weight_count={{len(numbers)}}",
        f"edge_count_estimate={{edge_count}}",
        f"path_cost={{path_cost}}",
    ],
    "numeric_results": {{
        "weight_count": len(numbers),
        "edge_count_estimate": edge_count,
        "path_cost": round(path_cost, 4),
        "node_count": len(path_nodes),
    }},
    "artifacts": ["result.json", "path_summary.json"],
    "next_steps": [
        "Provide an explicit graph or distance matrix for exact shortest-path or routing calculations.",
        "Add capacity or time-window data if this is a VRP-style task.",
    ],
}}
Path("result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
Path("path_summary.json").write_text(
    json.dumps(
        {{
            "weights": numbers[:20],
            "edge_count_estimate": edge_count,
            "path_cost": path_cost,
            "shortest_path": shortest_path,
        }},
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps(result, ensure_ascii=False))
"""
    return summary, code


def _build_evaluation_solver_code(context: dict[str, Any]) -> tuple[str, str]:
    context_json = json.dumps(context, ensure_ascii=False, indent=2)
    title = context["subproblem"]["title"]
    summary = f"Evaluation solver template generated a baseline result for {title}."
    code = f"""from __future__ import annotations
import json
import re
from pathlib import Path

context = {context_json}
subproblem = context["subproblem"]
analysis = subproblem["analysis"]
tables = [table for table in context.get("input_data", {{}}).get("tables", []) if table.get("kind") == "table"]
text = subproblem["text"] or context["problem_text"]
numbers = [float(x) for x in re.findall(r"-?\\d+(?:\\.\\d+)?", text)]
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
        task_roles = table.get("task_roles", {{}}).get("evaluation", {{}})
        weight_column = task_roles.get("weight") or table.get("column_roles", {{}}).get("weight")
        if weight_column is None:
            lower_map = {{str(column).lower(): str(column) for column in numeric_columns}}
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
result = {{
    "subproblem_title": subproblem["title"],
    "status": status,
    "method": analysis.get("chosen_method") or "evaluation_template_solver",
    "objective": analysis.get("objective") or "Produce a baseline evaluation summary.",
    "assumptions": analysis.get("assumptions") or ["Detected numbers are treated as rough indicator values."],
    "constraints": analysis.get("constraints") or ["Formal indicator definitions and weights still need confirmation."],
    "result_summary": f"Generated a baseline evaluation summary using {{library_used}}.",
    "evidence": [
        "template_used=baseline_evaluation_template",
        f"library_used={{library_used}}",
        f"table_name={{table_name or 'none'}}",
        f"score_column_count={{len(score_columns)}}",
        f"indicator_count={{indicator_count}}",
        f"number_count={{len(numbers)}}",
        f"average_score={{average_score}}",
    ],
    "numeric_results": {{
        "indicator_count": indicator_count,
        "number_count": len(numbers),
        "average_score": round(average_score, 4),
        "max_score": round(max_score, 4),
        "best_rank": best_rank,
    }},
    "artifacts": ["result.json", "evaluation_summary.json"],
    "next_steps": [
        "Add explicit indicator definitions and directions before formal ranking.",
        "Use AHP, entropy weighting, or TOPSIS once a complete indicator table is available.",
    ],
}}
Path("result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
Path("evaluation_summary.json").write_text(
    json.dumps(
        {{
            "numbers": numbers[:20],
            "average_score": average_score,
            "max_score": max_score,
            "normalized_scores": normalized[:20],
            "best_rank": best_rank,
            "indicator_count": indicator_count,
        }},
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps(result, ensure_ascii=False))
"""
    return summary, code


def _build_generic_solver_code(context: dict[str, Any]) -> tuple[str, str]:
    context_json = json.dumps(context, ensure_ascii=False, indent=2)
    subproblem = context["subproblem"]
    analysis = subproblem["analysis"]
    title = subproblem["title"]
    summary = f"Generic solver template generated a baseline result for {title}."
    code = f"""from __future__ import annotations
import json
import re
from pathlib import Path

context = {context_json}
subproblem = context["subproblem"]
analysis = subproblem["analysis"]
text = subproblem["text"] or context["problem_text"]
numbers = [float(x) for x in re.findall(r"-?\\d+(?:\\.\\d+)?", text)]
library_used = "stdlib"
if numbers:
    try:
        import numpy as np
    except Exception:
        np = None
    if np is not None:
        arr = np.array(numbers, dtype=float)
        mean_value = float(arr.mean())
        first_number = float(arr[0])
        library_used = "numpy"
    else:
        mean_value = float(sum(numbers) / len(numbers))
        first_number = float(numbers[0])
else:
    mean_value = 0.0
    first_number = "n/a"
status = "partial"
if numbers:
    status = "ok"
result = {{
    "subproblem_title": subproblem["title"],
    "status": status,
    "method": analysis.get("chosen_method") or "generic_template_solver",
    "objective": analysis.get("objective") or "Clarify objective before formal solving.",
    "assumptions": analysis.get("assumptions") or ["Use the current problem statement as the primary evidence source."],
    "constraints": analysis.get("constraints") or ["Formal constraints still need to be written explicitly."],
    "result_summary": (
        f"Created a structured baseline result with {{library_used}}. "
        + ("Detected numerical signals in the subproblem text." if numbers else "No direct numeric signal was found; more data is needed.")
    ),
    "evidence": [
        "template_used=baseline_structured_solver",
        f"library_used={{library_used}}",
        f"chosen_method={{analysis.get('chosen_method') or 'generic_template_solver'}}",
        f"number_count={{len(numbers)}}",
    ],
    "numeric_results": {{
        "detected_number_count": len(numbers),
        "first_number": first_number,
        "mean_value": round(mean_value, 4) if numbers else "n/a",
    }},
    "artifacts": ["result.json", "solver_notes.md"],
    "next_steps": [
        "Replace fallback logic with a domain-specific solver if numeric accuracy matters.",
        "Provide data tables or parameters for formal optimization or forecasting.",
    ],
}}
Path("result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
notes = [
    "# Solver Notes",
    "",
    f"- subproblem_title: {{result['subproblem_title']}}",
    f"- status: {{result['status']}}",
    f"- method: {{result['method']}}",
    f"- objective: {{result['objective']}}",
]
for item in result["constraints"]:
    notes.append(f"- constraint: {{item}}")
Path("solver_notes.md").write_text("\\n".join(notes), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
"""
    return summary, code


def _build_fallback_solver_code(context: dict[str, Any]) -> tuple[str, str]:
    task_type = _primary_task_type(context)
    if task_type == "预测/拟合":
        return _build_forecast_solver_code(context)
    if task_type == "优化/决策":
        return _build_optimization_solver_code(context)
    if task_type == "路径/网络":
        return _build_path_solver_code(context)
    if task_type == "评价/权重":
        return _build_evaluation_solver_code(context)
    return _build_generic_solver_code(context)


def _build_llm_solver(state: TaskState, subproblem: SubProblem, index: int) -> tuple[str, str]:
    context = _build_solver_context(state, subproblem, index)
    cfg = load_llm_config("CODING")
    if cfg is None:
        return _build_fallback_solver_code(context)

    llm = build_llm(cfg)
    response = llm.chat(
        [
            Message(role="system", content=render_prompt("coding_system")),
            Message(
                role="user",
                content=render_prompt(
                    "coding_user",
                    problem_text=state.problem_text,
                    context_json=json.dumps(context, ensure_ascii=False, indent=2),
                ),
            ),
        ],
        temperature=0.1,
    )
    try:
        payload = extract_first_json(response)
        if isinstance(payload, dict):
            summary = str(payload.get("summary") or "").strip() or f"Generated solver for {subproblem.title}."
            code = _extract_code_block(str(payload.get("code") or ""))
            if code:
                return summary, code
    except Exception:
        pass

    code = _extract_code_block(response)
    if code:
        return f"Generated solver for {subproblem.title}.", code
    return _build_fallback_solver_code(context)


def _required_report_sections() -> list[str]:
    return [
        "# 摘要",
        "# 问题重述",
        "# 子问题分析与方法选择",
        "# 模型假设与符号说明",
        "# 求解与实验",
        "# 结果与分析",
        "# 结论与后续工作",
    ]


def _required_report_sections() -> list[str]:
    return required_report_titles()


def _append_finding(findings: list[dict[str, str]], *, severity: str, area: str, message: str, suggestion: str) -> None:
    findings.append(
        {
            "severity": severity,
            "area": area,
            "message": message,
            "suggestion": suggestion,
        }
    )


def _summarize_solver_runs(runs: list[SolverRun]) -> str:
    if not runs:
        return "No solver runs were produced."
    lines: list[str] = []
    for run in runs:
        status = run.structured_result.get("status") or "invalid"
        summary = run.structured_result.get("result_summary") or run.summary
        lines.append(f"{run.subproblem_title}: {status} - {summary}")
    return "\n".join(lines)


def _overall_solver_status(runs: list[SolverRun]) -> str:
    if not runs:
        return "solver_failed"
    if any(not run.success or not run.schema_valid for run in runs):
        return "solver_failed"
    statuses = {str(run.structured_result.get("status") or "") for run in runs}
    if statuses == {"ok"}:
        return "solved"
    if "failed" in statuses:
        return "solver_failed"
    return "partially_solved"


@dataclass(frozen=True)
class ModelingAgent:
    name: str = "modeling"

    def run(self, state: TaskState, tools: ToolRegistry, memory: MemoryStore) -> TaskState:
        state = ProblemDecomposeSkill().run(state, tools)
        state = SubProblemAnalyzeSkill().run(state, tools)
        state = ClarifySkill().run(state, tools)
        state = ModelSkill().run(state, tools)

        cfg = load_llm_config("MODELING")
        if cfg is not None:
            llm = build_llm(cfg)
            try:
                payload = extract_first_json(
                    llm.chat(
                        [
                            Message(role="system", content=render_prompt("modeling_system")),
                            Message(
                                role="user",
                                content=render_prompt(
                                    "modeling_user",
                                    problem_text=state.problem_text,
                                ),
                            ),
                        ],
                        temperature=0.2,
                    )
                )
                if isinstance(payload, list) and payload:
                    state.subproblems = []
                    for index, item in enumerate(payload, start=1):
                        if not isinstance(item, dict):
                            continue
                        subproblem = SubProblem(
                            title=str(item.get("title") or f"Subproblem {index}").strip(),
                            text=str(item.get("text") or "").strip(),
                        )
                        analysis = subproblem.analysis
                        analysis.task_types = _string_list(item.get("task_types"))
                        analysis.candidate_models = _string_list(item.get("candidate_models"))
                        analysis.solution_plan = _string_list(item.get("solution_plan"))
                        analysis.key_variables = _string_list(item.get("key_variables"))
                        analysis.needed_data = _string_list(item.get("needed_data"))
                        analysis.evaluation = _string_list(item.get("evaluation"))
                        analysis.notes = _string_list(item.get("notes"))
                        analysis.objective = str(item.get("objective") or "").strip() or None
                        analysis.constraints = _string_list(item.get("constraints"))
                        analysis.assumptions = _string_list(item.get("assumptions"))
                        analysis.deliverables = _string_list(item.get("deliverables"))
                        analysis.formulation_steps = _string_list(item.get("formulation_steps"))
                        analysis.chosen_method = str(item.get("chosen_method") or "").strip() or None
                        if isinstance(item.get("confidence"), (float, int)):
                            analysis.confidence = float(item["confidence"])
                        state.subproblems.append(subproblem)
                    state = ClarifySkill().run(state, tools)
                    state = ModelSkill().run(state, tools)
            except Exception as exc:
                memory.set_agent_json(self.name, "llm_error", {"error": str(exc)})
                memory.append_event("agent", self.name, "llm_error", {"error": str(exc)})

        memory.set_shared("problem_text", state.problem_text)
        memory.set_shared_json("subproblems", _subproblems_payload(state))
        memory.set_agent_json(self.name, "clarifications", state.clarifications)
        memory.set_agent_json(
            self.name,
            "model_overview",
            {
                "chosen_method": state.model.chosen_method,
                "method_candidates": state.model.method_candidates,
                "assumptions": state.model.assumptions,
                "constraints": state.model.constraints,
                "formulation_outline": state.model.formulation_outline,
            },
        )
        memory.append_event("agent", self.name, "done", {"stage": state.stage})
        return state


@dataclass(frozen=True)
class CodingAgent:
    name: str = "coding"

    def run(self, state: TaskState, tools: ToolRegistry, memory: MemoryStore) -> TaskState:
        tool = tools.maybe_get("python_exec")
        if tool is None:
            state.results["status"] = "solver_unavailable"
            state.results["solver_summary"] = "No python execution tool is registered."
            state = SolveSkill().run(state, tools)
            memory.set_agent_json(
                self.name,
                "solver_result",
                {"status": state.results.get("status"), "summary": state.results.get("solver_summary")},
            )
            memory.append_event("agent", self.name, "done", {"stage": state.stage})
            return state

        state.solver_runs = []
        structured_results: list[dict[str, Any]] = []
        for index, subproblem in enumerate(state.subproblems, start=1):
            generation_error = ""
            try:
                summary, code = _build_llm_solver(state, subproblem, index)
            except Exception as exc:
                summary, code = _build_fallback_solver_code(_build_solver_context(state, subproblem, index))
                generation_error = str(exc)

            result = tool.run(
                {
                    "code": code,
                    "filename": f"solver_{index}.py",
                    "context": _build_solver_context(state, subproblem, index),
                    "timeout_s": 20.0,
                }
            )
            run_success = bool(result.get("success"))
            schema_valid, structured_result, schema_error = _extract_structured_result(
                str(result.get("run_dir") or ""),
                [str(name) for name in result.get("artifacts") or []],
                str(result.get("stdout") or ""),
                subproblem.title,
            )
            if generation_error:
                stderr_text = str(result.get("stderr") or "") + f"\nRecovered from CODING generation failure: {generation_error}"
            else:
                stderr_text = str(result.get("stderr") or "")

            if not run_success and not structured_result:
                structured_result = {
                    "subproblem_title": subproblem.title,
                    "status": "failed",
                    "method": subproblem.analysis.chosen_method or "unknown",
                    "objective": subproblem.analysis.objective or "",
                    "assumptions": subproblem.analysis.assumptions,
                    "constraints": subproblem.analysis.constraints,
                    "result_summary": "Execution failed before a structured result was produced.",
                    "evidence": ["python_exec returned a non-zero exit status"],
                    "numeric_results": {},
                    "artifacts": [str(name) for name in result.get("artifacts") or []],
                    "next_steps": ["Inspect stderr and generated code before retrying."],
                }

            solver_run = SolverRun(
                subproblem_title=subproblem.title,
                success=run_success and schema_valid and structured_result.get("status") in {"ok", "partial"},
                summary=summary,
                code=code,
                stdout=str(result.get("stdout") or ""),
                stderr=(stderr_text + (f"\nSchema validation failed: {schema_error}" if schema_error else "")).strip(),
                artifacts=[str(name) for name in result.get("artifacts") or []],
                structured_result=structured_result,
                schema_valid=schema_valid,
            )
            state.solver_runs.append(solver_run)
            structured_results.append(structured_result)
            state.artifacts.extend(_load_solver_artifacts(str(result.get("run_dir") or ""), solver_run.artifacts))

        state.results["structured_solver_results"] = structured_results
        state.results["status"] = _overall_solver_status(state.solver_runs)
        state.results["solver_summary"] = _summarize_solver_runs(state.solver_runs)
        state.results["solved_subproblems"] = [
            run.subproblem_title
            for run in state.solver_runs
            if run.schema_valid and run.structured_result.get("status") == "ok"
        ]
        state.results["partial_subproblems"] = [
            run.subproblem_title
            for run in state.solver_runs
            if run.schema_valid and run.structured_result.get("status") == "partial"
        ]
        state = SolveSkill().run(state, tools)
        memory.set_agent_json(
            self.name,
            "solver_result",
            {
                "status": state.results.get("status"),
                "summary": state.results.get("solver_summary"),
                "runs": _solver_runs_payload(state),
            },
        )
        memory.append_event("agent", self.name, "done", {"stage": state.stage})
        return state


@dataclass(frozen=True)
class ReviewAgent:
    name: str = "review"

    def run(self, state: TaskState, tools: ToolRegistry, memory: MemoryStore) -> TaskState:
        state = ValidateSkill().run(state, tools)

        findings: list[dict[str, str]] = []
        for subproblem in state.subproblems:
            analysis = subproblem.analysis
            if not analysis.objective:
                _append_finding(
                    findings,
                    severity="medium",
                    area=subproblem.title,
                    message=f"{subproblem.title} is missing an explicit objective.",
                    suggestion="Add a clear objective or target output for this subproblem.",
                )
            if not analysis.chosen_method:
                _append_finding(
                    findings,
                    severity="medium",
                    area=subproblem.title,
                    message=f"{subproblem.title} does not have a chosen primary method.",
                    suggestion="Pick one main method from the candidate list and justify it.",
                )
            if not analysis.constraints:
                _append_finding(
                    findings,
                    severity="low",
                    area=subproblem.title,
                    message=f"{subproblem.title} still lacks explicit constraints.",
                    suggestion="Translate hard and soft constraints from the problem statement into a list.",
                )

        if not state.solver_runs:
            _append_finding(
                findings,
                severity="high",
                area="coding",
                message="No executable solver runs were recorded.",
                suggestion="Run Coding again after improving the solver prompt or input data.",
            )
        else:
            for run in state.solver_runs:
                if not run.schema_valid:
                    _append_finding(
                        findings,
                        severity="high",
                        area="coding",
                        message=f"{run.subproblem_title} did not produce a valid structured result schema.",
                        suggestion="Require the generated code to write a valid result.json before marking success.",
                    )
                elif run.structured_result.get("status") == "partial":
                    _append_finding(
                        findings,
                        severity="medium",
                        area="coding",
                        message=f"{run.subproblem_title} only has a partial structured result.",
                        suggestion="Replace the baseline/fallback logic with a domain-specific solver or add more data.",
                    )
                elif run.structured_result.get("status") == "failed":
                    _append_finding(
                        findings,
                        severity="high",
                        area="coding",
                        message=f"{run.subproblem_title} returned a failed structured result.",
                        suggestion="Inspect the generated code, stderr, and result.json for this subproblem.",
                    )

        if state.report_md is not None:
            if "## " not in state.report_md:
                _append_finding(
                    findings,
                    severity="medium",
                    area="writing",
                    message="The report is missing detailed subsection headings.",
                    suggestion="Add per-subproblem subsections and a dedicated results section.",
                )
            for run in state.solver_runs:
                if run.subproblem_title not in state.report_md:
                    _append_finding(
                        findings,
                        severity="low",
                        area="writing",
                        message=f"The report does not explicitly mention {run.subproblem_title}.",
                        suggestion="Add a short paragraph summarizing the structured result for that subproblem.",
                    )

        review_notes = list(state.results.get("review_notes", []))
        if findings:
            review_notes.append(f"Identified {len(findings)} review findings.")
        else:
            review_notes.append("No major structural issues were detected.")

        state.results["review_findings"] = findings
        state.results["review_notes"] = review_notes
        if state.report_md is None:
            state.results["reviewed_solution"] = True
            state.stage = "report"
        else:
            state.results["report_checks"] = _required_report_sections()
            state.results["final_review_done"] = True
            state.stage = "done"

        memory.set_agent_json(
            self.name,
            "review",
            {
                "checks": state.results.get("checks", []),
                "notes": review_notes,
                "report_checks": state.results.get("report_checks", []),
                "findings": findings,
            },
        )
        memory.append_event("agent", self.name, "done", {"stage": state.stage})
        return state


@dataclass(frozen=True)
class WritingAgent:
    name: str = "writing"

    def run(self, state: TaskState, tools: ToolRegistry, memory: MemoryStore) -> TaskState:
        cfg = load_llm_config("WRITING")
        if cfg is not None:
            llm = build_llm(cfg)
            try:
                report = llm.chat(
                    [
                        Message(role="system", content=render_prompt("writing_system")),
                        Message(
                            role="user",
                            content=render_prompt(
                                "writing_user",
                                problem_text=state.problem_text,
                                subproblems_json=json.dumps(_subproblems_payload(state), ensure_ascii=False, indent=2),
                                solver_runs_json=json.dumps(_solver_runs_payload(state), ensure_ascii=False, indent=2),
                                review_findings_json=json.dumps(
                                    state.results.get("review_findings", []),
                                    ensure_ascii=False,
                                    indent=2,
                                ),
                            ),
                        ),
                    ],
                    temperature=0.2,
                )
                state.report_md = report.strip()
            except Exception as exc:
                memory.set_agent_json(self.name, "llm_error", {"error": str(exc)})
                memory.append_event("agent", self.name, "llm_error", {"error": str(exc)})
                state = ReportSkill().run(state, tools)
        else:
            state = ReportSkill().run(state, tools)

        if state.report_md is not None:
            memory.set_shared("report_md", state.report_md)
            state.stage = "review"
        memory.append_event("agent", self.name, "done", {"stage": state.stage})
        return state
