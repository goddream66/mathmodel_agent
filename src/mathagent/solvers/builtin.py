from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from .base import SolverRegistry, SolverSpec


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


def _looks_like_geometry_problem(context: dict[str, Any]) -> bool:
    subproblem = context.get("subproblem", {})
    analysis = subproblem.get("analysis", {})
    text_parts = [
        str(context.get("problem_text") or ""),
        str(subproblem.get("title") or ""),
        str(subproblem.get("text") or ""),
        str(analysis.get("objective") or ""),
        str(analysis.get("chosen_method") or ""),
        " ".join(str(item) for item in analysis.get("task_types", []) if str(item).strip()),
        " ".join(str(item) for item in analysis.get("candidate_models", []) if str(item).strip()),
        " ".join(str(item) for item in analysis.get("key_variables", []) if str(item).strip()),
    ]
    normalized = " ".join(text_parts).lower()
    keywords = (
        "bearing",
        "angle",
        "angles",
        "azimuth",
        "triang",
        "localiz",
        "coordinate",
        "coordinates",
        "position",
        "geometry",
        "formation",
        "drone",
        "uav",
        "anchor",
        "sensor",
        "radius",
        "circle",
        "定位",
        "方位",
        "角度",
        "坐标",
        "几何",
        "编队",
        "无人机",
        "阵型",
        "圆形",
        "锚点",
        "测角",
        "三角",
    )
    if any(keyword in normalized for keyword in keywords):
        return True
    raw_text = f"{context.get('problem_text') or ''}\n{subproblem.get('text') or ''}"
    return len(re.findall(r"\([-+]?\d+(?:\.\d+)?,\s*[-+]?\d+(?:\.\d+)?\)", raw_text)) >= 2 and bool(
        re.search(r"[-+]?\d+(?:\.\d+)?\s*(?:deg|degree|degrees|°|度)", raw_text, re.IGNORECASE)
    )


def _build_geometry_solver_code(context: dict[str, Any]) -> tuple[str, str]:
    context_json = json.dumps(context, ensure_ascii=False, indent=2)
    title = context["subproblem"]["title"]
    summary = f"Geometry solver template generated a structured result for {title}."
    code = f"""from __future__ import annotations
import json
import math
import re
from pathlib import Path

context = {context_json}
subproblem = context["subproblem"]
analysis = subproblem["analysis"]
tables = [table for table in context.get("input_data", {{}}).get("tables", []) if table.get("kind") == "table"]
text = subproblem["text"] or context["problem_text"]

def _wrap_angle_deg(value):
    return (float(value) + 180.0) % 360.0 - 180.0

def _bearing_deg(ax, ay, px, py):
    return math.degrees(math.atan2(py - ay, px - ax))

def _coord_columns(columns):
    lower_map = {{str(column).lower(): str(column) for column in columns}}
    x_col = lower_map.get("x") or lower_map.get("coord_x") or lower_map.get("longitude") or lower_map.get("lon")
    y_col = lower_map.get("y") or lower_map.get("coord_y") or lower_map.get("latitude") or lower_map.get("lat")
    label_col = lower_map.get("name") or lower_map.get("id") or lower_map.get("label") or lower_map.get("point")
    return x_col, y_col, label_col

def _extract_points_from_tables():
    for table in tables:
        x_col, y_col, label_col = _coord_columns(table.get("columns", []))
        if not (x_col and y_col):
            continue
        points = []
        for index, row in enumerate(table.get("rows", []), start=1):
            x_value = row.get(x_col)
            y_value = row.get(y_col)
            if not isinstance(x_value, (int, float)) or not isinstance(y_value, (int, float)):
                continue
            label = row.get(label_col) if label_col else None
            label = str(label).strip() if label not in {{None, ""}} else f"P{{index}}"
            points.append({{"label": label, "x": float(x_value), "y": float(y_value)}})
        if points:
            return table.get("name", "table"), points
    return None, []

def _extract_angle_rows():
    for table in tables:
        columns = list(table.get("columns", []))
        lower_map = {{str(column).lower(): str(column) for column in columns}}
        angle_col = lower_map.get("angle") or lower_map.get("bearing") or lower_map.get("azimuth") or lower_map.get("theta")
        if angle_col is None:
            continue
        x_col, y_col, label_col = _coord_columns(columns)
        rows = []
        for index, row in enumerate(table.get("rows", []), start=1):
            angle_value = row.get(angle_col)
            if not isinstance(angle_value, (int, float)):
                continue
            if x_col and y_col and isinstance(row.get(x_col), (int, float)) and isinstance(row.get(y_col), (int, float)):
                label = row.get(label_col) if label_col else None
                label = str(label).strip() if label not in {{None, ""}} else f"M{{index}}"
                rows.append(
                    {{
                        "label": label,
                        "x": float(row[x_col]),
                        "y": float(row[y_col]),
                        "angle_deg": float(angle_value),
                    }}
                )
        if rows:
            return table.get("name", "table"), rows
    return None, []

table_name, points = _extract_points_from_tables()
angle_table_name, angle_rows = _extract_angle_rows()
coord_pairs = [
    (float(x), float(y))
    for x, y in re.findall(r"\\(([-+]?\\d+(?:\\.\\d+)?),\\s*([-+]?\\d+(?:\\.\\d+)?)\\)", text)
]
text_angles = [
    float(value)
    for value in re.findall(r"([-+]?\\d+(?:\\.\\d+)?)\\s*(?:deg|degree|degrees|°|度)", text, re.IGNORECASE)
]

if not points and coord_pairs:
    points = [{{"label": f"P{{index + 1}}", "x": pair[0], "y": pair[1]}} for index, pair in enumerate(coord_pairs)]

measurements = []
if angle_rows:
    measurements = list(angle_rows)
elif points and text_angles:
    usable = min(len(points), len(text_angles))
    measurements = [
        {{
            "label": points[index]["label"],
            "x": points[index]["x"],
            "y": points[index]["y"],
            "angle_deg": float(text_angles[index]),
        }}
        for index in range(usable)
    ]

def _grid_search(measurements, seed_x, seed_y, scale):
    best = None
    for step_divisor in (6.0, 18.0, 48.0):
        step = max(scale / step_divisor, 0.25)
        span = max(scale, 1.0)
        if best is None:
            center_x, center_y = seed_x, seed_y
        else:
            center_x, center_y = best[1], best[2]
            span = max(step * 6.0, 1.0)
        candidate = None
        for ix in range(-6, 7):
            for iy in range(-6, 7):
                px = center_x + ix * step
                py = center_y + iy * step
                residuals = []
                for item in measurements:
                    predicted = _bearing_deg(item["x"], item["y"], px, py)
                    residuals.append(_wrap_angle_deg(predicted - item["angle_deg"]))
                score = sum(value * value for value in residuals) / max(len(residuals), 1)
                if candidate is None or score < candidate[0]:
                    candidate = (score, px, py, residuals)
        best = candidate
    return best

library_used = "stdlib_grid_search"
solver_mode = "formation_summary"
status = "partial"
estimated_x = None
estimated_y = None
mean_residual_deg = None
max_residual_deg = None
formation_center_x = None
formation_center_y = None
formation_radius = None

if len(measurements) >= 2:
    xs = [item["x"] for item in measurements]
    ys = [item["y"] for item in measurements]
    seed_x = sum(xs) / len(xs)
    seed_y = sum(ys) / len(ys)
    scale = max(max(xs) - min(xs), max(ys) - min(ys), 10.0)
    try:
        from scipy.optimize import least_squares
    except Exception:
        least_squares = None
    if least_squares is not None:
        def _residuals(candidate):
            px, py = candidate
            return [
                _wrap_angle_deg(_bearing_deg(item["x"], item["y"], px, py) - item["angle_deg"])
                for item in measurements
            ]
        result = least_squares(_residuals, x0=[seed_x, seed_y])
        estimated_x = float(result.x[0])
        estimated_y = float(result.x[1])
        residual_values = [float(value) for value in _residuals((estimated_x, estimated_y))]
        library_used = "scipy_least_squares"
    else:
        best = _grid_search(measurements, seed_x, seed_y, scale)
        estimated_x = float(best[1])
        estimated_y = float(best[2])
        residual_values = [float(value) for value in best[3]]
    mean_residual_deg = float(sum(abs(value) for value in residual_values) / len(residual_values))
    max_residual_deg = float(max(abs(value) for value in residual_values))
    status = "ok"
    solver_mode = "bearing_triangulation"
elif len(points) >= 3:
    xs = [item["x"] for item in points]
    ys = [item["y"] for item in points]
    formation_center_x = float(sum(xs) / len(xs))
    formation_center_y = float(sum(ys) / len(ys))
    formation_radius = float(
        sum(math.hypot(item["x"] - formation_center_x, item["y"] - formation_center_y) for item in points) / len(points)
    )
    status = "partial"
    solver_mode = "formation_summary"

figure_title = f"{{subproblem['title']}}: geometry layout and estimated position"
figure_file = "geometry_layout.svg"

def _write_layout(path):
    plot_points = [{{"x": item["x"], "y": item["y"], "label": item["label"], "kind": "anchor"}} for item in points]
    if estimated_x is not None and estimated_y is not None:
        plot_points.append({{"x": estimated_x, "y": estimated_y, "label": "Estimated", "kind": "estimate"}})
    elif formation_center_x is not None and formation_center_y is not None:
        plot_points.append({{"x": formation_center_x, "y": formation_center_y, "label": "Center", "kind": "estimate"}})
    if not plot_points:
        plot_points = [{{"x": 0.0, "y": 0.0, "label": "N/A", "kind": "anchor"}}]
    xs = [item["x"] for item in plot_points]
    ys = [item["y"] for item in plot_points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    if min_x == max_x:
        max_x = min_x + 1.0
    if min_y == max_y:
        max_y = min_y + 1.0
    padding_x = max((max_x - min_x) * 0.2, 1.0)
    padding_y = max((max_y - min_y) * 0.2, 1.0)
    min_x -= padding_x
    max_x += padding_x
    min_y -= padding_y
    max_y += padding_y
    width = 720
    height = 420
    left = 60
    top = 50
    right = 40
    bottom = 50
    plot_w = width - left - right
    plot_h = height - top - bottom
    def _xy(px, py):
        x = left + (px - min_x) * plot_w / (max_x - min_x)
        y = top + plot_h * (1.0 - (py - min_y) / (max_y - min_y))
        return x, y
    circles = []
    labels = []
    rays = []
    for item in plot_points:
        x, y = _xy(item["x"], item["y"])
        fill = "#dc2626" if item["kind"] == "estimate" else "#2563eb"
        radius = 6 if item["kind"] == "estimate" else 5
        circles.append(f"<circle cx='{{x:.1f}}' cy='{{y:.1f}}' r='{{radius}}' fill='{{fill}}' />")
        labels.append(f"<text x='{{x + 8:.1f}}' y='{{y - 8:.1f}}' font-size='12' fill='#111827'>{{item['label']}}</text>")
    target_x = estimated_x if estimated_x is not None else formation_center_x
    target_y = estimated_y if estimated_y is not None else formation_center_y
    if target_x is not None and target_y is not None:
        tx, ty = _xy(target_x, target_y)
        for item in measurements:
            ax, ay = _xy(item["x"], item["y"])
            rays.append(f"<line x1='{{ax:.1f}}' y1='{{ay:.1f}}' x2='{{tx:.1f}}' y2='{{ty:.1f}}' stroke='#94a3b8' stroke-dasharray='6 4' />")
    svg = f\"\"\"<svg xmlns='http://www.w3.org/2000/svg' width='{{width}}' height='{{height}}' viewBox='0 0 {{width}} {{height}}'>
<rect width='100%' height='100%' fill='white'/>
<text x='{{width/2:.1f}}' y='28' font-size='22' text-anchor='middle' fill='#111827'>{{figure_title}}</text>
<rect x='{{left}}' y='{{top}}' width='{{plot_w}}' height='{{plot_h}}' fill='#f8fafc' stroke='#cbd5e1'/>
{{''.join(rays)}}
{{''.join(circles)}}
{{''.join(labels)}}
</svg>\"\"\"
    Path(path).write_text(svg, encoding="utf-8")

_write_layout(figure_file)

numeric_results = {{
    "point_count": len(points),
    "measurement_count": len(measurements),
}}
if estimated_x is not None and estimated_y is not None:
    numeric_results["estimated_x"] = round(estimated_x, 4)
    numeric_results["estimated_y"] = round(estimated_y, 4)
if mean_residual_deg is not None:
    numeric_results["mean_residual_deg"] = round(mean_residual_deg, 4)
if max_residual_deg is not None:
    numeric_results["max_residual_deg"] = round(max_residual_deg, 4)
if formation_center_x is not None and formation_center_y is not None:
    numeric_results["center_x"] = round(formation_center_x, 4)
    numeric_results["center_y"] = round(formation_center_y, 4)
if formation_radius is not None:
    numeric_results["radius_estimate"] = round(formation_radius, 4)

result = {{
    "subproblem_title": subproblem["title"],
    "status": status,
    "method": analysis.get("chosen_method") or "geometry_localization_template_solver",
    "objective": analysis.get("objective") or "Estimate a geometric target position or summarize the current formation.",
    "assumptions": analysis.get("assumptions") or ["Angles and coordinates are interpreted in a common 2D plane."],
    "constraints": analysis.get("constraints") or ["Additional geometric measurements may be required for a unique exact solution."],
    "result_summary": f"Generated a geometry-focused structured result using {{solver_mode}} with {{library_used}}.",
    "evidence": [
        "template_used=geometry_localization_template",
        f"solver_mode={{solver_mode}}",
        f"library_used={{library_used}}",
        f"point_count={{len(points)}}",
        f"measurement_count={{len(measurements)}}",
        f"table_name={{table_name or angle_table_name or 'none'}}",
    ],
    "numeric_results": numeric_results,
    "figure_titles": [figure_title],
    "artifacts": ["result.json", "geometry_summary.json", figure_file],
    "next_steps": [
        "Provide more anchor or angle measurements if a more stable localization result is required.",
        "Add explicit geometric constraints such as equal-distance or formation spacing for a stronger solver.",
    ],
}}

Path("result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
Path("geometry_summary.json").write_text(
    json.dumps(
        {{
            "points": points,
            "measurements": measurements,
            "estimated_x": estimated_x,
            "estimated_y": estimated_y,
            "mean_residual_deg": mean_residual_deg,
            "max_residual_deg": max_residual_deg,
            "formation_center_x": formation_center_x,
            "formation_center_y": formation_center_y,
            "formation_radius": formation_radius,
        }},
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps(result, ensure_ascii=False))
"""
    return summary, code


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

figure_title = f"{{subproblem['title']}}：历史序列与预测结果"
figure_file = "forecast_plot.svg"

def _write_line_chart(path, title, history, forecast):
    points = history + [forecast]
    if not points:
        return
    width = 720
    height = 420
    left = 70
    right = 30
    top = 50
    bottom = 60
    plot_w = width - left - right
    plot_h = height - top - bottom
    ymin = min(points)
    ymax = max(points)
    if ymax == ymin:
        ymax = ymin + 1.0
    def _xy(index, value, total):
        span = max(total - 1, 1)
        x = left + plot_w * index / span
        y = top + plot_h * (1.0 - (value - ymin) / (ymax - ymin))
        return x, y
    history_points = [_xy(i, value, len(points)) for i, value in enumerate(history)]
    forecast_point = _xy(len(points) - 1, forecast, len(points))
    forecast_start = history_points[-1] if history_points else forecast_point
    x_axis_labels = "".join(
        f"<text x='{{_xy(i, points[i], len(points))[0]:.1f}}' y='380' font-size='12' text-anchor='middle'>t{{i + 1}}</text>"
        for i in range(len(points))
    )
    y_ticks = []
    for tick in range(5):
        value = ymin + (ymax - ymin) * tick / 4
        y = top + plot_h * (1 - tick / 4)
        y_ticks.append(
            f"<line x1='{{left}}' y1='{{y:.1f}}' x2='{{width-right}}' y2='{{y:.1f}}' stroke='#e5e7eb' />"
            f"<text x='{{left-12}}' y='{{y+4:.1f}}' font-size='12' text-anchor='end'>{{value:.2f}}</text>"
        )
    history_polyline = " ".join(f"{{x:.1f}},{{y:.1f}}" for x, y in history_points)
    svg = f\"\"\"<svg xmlns='http://www.w3.org/2000/svg' width='{{width}}' height='{{height}}' viewBox='0 0 {{width}} {{height}}'>
<rect width='100%' height='100%' fill='white'/>
<text x='{{width/2:.1f}}' y='28' font-size='22' text-anchor='middle' fill='#111827'>{{title}}</text>
<line x1='{{left}}' y1='{{height-bottom}}' x2='{{width-right}}' y2='{{height-bottom}}' stroke='#111827' stroke-width='2'/>
<line x1='{{left}}' y1='{{top}}' x2='{{left}}' y2='{{height-bottom}}' stroke='#111827' stroke-width='2'/>
{{''.join(y_ticks)}}
<polyline points='{{history_polyline}}' fill='none' stroke='#2563eb' stroke-width='3'/>
<line x1='{{forecast_start[0]:.1f}}' y1='{{forecast_start[1]:.1f}}' x2='{{forecast_point[0]:.1f}}' y2='{{forecast_point[1]:.1f}}' stroke='#dc2626' stroke-width='3' stroke-dasharray='8 6'/>
<circle cx='{{forecast_point[0]:.1f}}' cy='{{forecast_point[1]:.1f}}' r='5' fill='#dc2626'/>
<text x='{{forecast_point[0]:.1f}}' y='{{forecast_point[1]-12:.1f}}' font-size='12' text-anchor='middle' fill='#dc2626'>forecast={{forecast:.2f}}</text>
{{x_axis_labels}}
</svg>\"\"\"
    Path(path).write_text(svg, encoding="utf-8")

_write_line_chart(figure_file, figure_title, series, forecast_value)

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
    "figure_titles": [figure_title],
    "artifacts": ["result.json", "forecast_metrics.json", figure_file],
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
figure_title = f"{{subproblem['title']}}：候选成本与入选方案对比"
figure_file = "optimization_plan.svg"

def _write_bar_chart(path, title, candidates, selected):
    values = list(candidates[:8]) or [0.0]
    selected_values = list(selected[:8])
    width = 720
    height = 420
    left = 70
    top = 60
    bottom = 60
    chart_h = height - top - bottom
    max_value = max(values + selected_values + [1.0])
    step = 70
    bars = []
    labels = []
    for index, value in enumerate(values):
        x = left + index * step
        bar_h = chart_h * value / max_value
        y = top + chart_h - bar_h
        fill = "#2563eb" if value not in selected_values else "#dc2626"
        bars.append(f"<rect x='{{x}}' y='{{y:.1f}}' width='32' height='{{bar_h:.1f}}' fill='{{fill}}' rx='4'/>")
        labels.append(f"<text x='{{x + 16}}' y='380' font-size='12' text-anchor='middle'>c{{index + 1}}</text>")
        labels.append(f"<text x='{{x + 16}}' y='{{y - 8:.1f}}' font-size='12' text-anchor='middle'>{{value:.1f}}</text>")
    svg = f\"\"\"<svg xmlns='http://www.w3.org/2000/svg' width='{{width}}' height='{{height}}' viewBox='0 0 {{width}} {{height}}'>
<rect width='100%' height='100%' fill='white'/>
<text x='{{width/2:.1f}}' y='28' font-size='22' text-anchor='middle' fill='#111827'>{{title}}</text>
<line x1='{{left-10}}' y1='{{height-bottom}}' x2='{{width-30}}' y2='{{height-bottom}}' stroke='#111827' stroke-width='2'/>
    {{''.join(bars)}}
    {{''.join(labels)}}
</svg>\"\"\"
    Path(path).write_text(svg, encoding="utf-8")

_write_bar_chart(figure_file, figure_title, candidate_costs, selected_costs)
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
    "figure_titles": [figure_title],
    "artifacts": ["result.json", "optimization_summary.json", figure_file],
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
figure_title = f"{{subproblem['title']}}：路径权重与总代价示意"
figure_file = "path_summary.svg"

def _write_weight_chart(path, title, weights, total_cost):
    values = list(weights[:8]) or [0.0]
    width = 720
    height = 420
    left = 70
    top = 60
    bottom = 60
    chart_h = height - top - bottom
    max_value = max(values + [float(total_cost or 0.0), 1.0])
    step = 70
    bars = []
    labels = []
    for index, value in enumerate(values):
        x = left + index * step
        bar_h = chart_h * float(value) / max_value
        y = top + chart_h - bar_h
        bars.append(f"<rect x='{{x}}' y='{{y:.1f}}' width='32' height='{{bar_h:.1f}}' fill='#0f766e' rx='4'/>")
        labels.append(f"<text x='{{x + 16}}' y='380' font-size='12' text-anchor='middle'>w{{index + 1}}</text>")
    svg = f\"\"\"<svg xmlns='http://www.w3.org/2000/svg' width='{{width}}' height='{{height}}' viewBox='0 0 {{width}} {{height}}'>
<rect width='100%' height='100%' fill='white'/>
<text x='{{width/2:.1f}}' y='28' font-size='22' text-anchor='middle' fill='#111827'>{{title}}</text>
<text x='{{width-40}}' y='50' font-size='14' text-anchor='end' fill='#111827'>total={{total_cost:.2f}}</text>
<line x1='{{left-10}}' y1='{{height-bottom}}' x2='{{width-30}}' y2='{{height-bottom}}' stroke='#111827' stroke-width='2'/>
{{''.join(bars)}}
{{''.join(labels)}}
</svg>\"\"\"
    Path(path).write_text(svg, encoding="utf-8")

_write_weight_chart(figure_file, figure_title, numbers, path_cost)
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
    "figure_titles": [figure_title],
    "artifacts": ["result.json", "path_summary.json", figure_file],
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
figure_title = f"{{subproblem['title']}}：评价指标得分分布"
figure_file = "evaluation_scores.svg"

def _write_score_chart(path, title, scores):
    values = list(scores[:8]) or [0.0]
    width = 720
    height = 420
    left = 70
    top = 60
    bottom = 60
    chart_h = height - top - bottom
    max_value = max(values + [1.0])
    step = 70
    bars = []
    labels = []
    for index, value in enumerate(values):
        x = left + index * step
        bar_h = chart_h * float(value) / max_value
        y = top + chart_h - bar_h
        bars.append(f"<rect x='{{x}}' y='{{y:.1f}}' width='32' height='{{bar_h:.1f}}' fill='#7c3aed' rx='4'/>")
        labels.append(f"<text x='{{x + 16}}' y='380' font-size='12' text-anchor='middle'>s{{index + 1}}</text>")
    svg = f\"\"\"<svg xmlns='http://www.w3.org/2000/svg' width='{{width}}' height='{{height}}' viewBox='0 0 {{width}} {{height}}'>
<rect width='100%' height='100%' fill='white'/>
<text x='{{width/2:.1f}}' y='28' font-size='22' text-anchor='middle' fill='#111827'>{{title}}</text>
<line x1='{{left-10}}' y1='{{height-bottom}}' x2='{{width-30}}' y2='{{height-bottom}}' stroke='#111827' stroke-width='2'/>
{{''.join(bars)}}
{{''.join(labels)}}
</svg>\"\"\"
    Path(path).write_text(svg, encoding="utf-8")

_write_score_chart(figure_file, figure_title, numbers)
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
    "figure_titles": [figure_title],
    "artifacts": ["result.json", "evaluation_summary.json", figure_file],
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
figure_title = f"{{subproblem['title']}}：关键数值概览"
figure_file = "solver_summary.svg"

def _write_generic_chart(path, title, values):
    bars = list(values[:8]) or [0.0]
    width = 720
    height = 420
    left = 70
    top = 60
    bottom = 60
    chart_h = height - top - bottom
    max_value = max([abs(float(v)) for v in bars] + [1.0])
    step = 70
    rects = []
    labels = []
    for index, value in enumerate(bars):
        numeric = float(value)
        bar_h = chart_h * abs(numeric) / max_value
        x = left + index * step
        y = top + chart_h - bar_h
        rects.append(f"<rect x='{{x}}' y='{{y:.1f}}' width='32' height='{{bar_h:.1f}}' fill='#2563eb' rx='4'/>")
        labels.append(f"<text x='{{x + 16}}' y='380' font-size='12' text-anchor='middle'>n{{index + 1}}</text>")
    svg = f\"\"\"<svg xmlns='http://www.w3.org/2000/svg' width='{{width}}' height='{{height}}' viewBox='0 0 {{width}} {{height}}'>
<rect width='100%' height='100%' fill='white'/>
<text x='{{width/2:.1f}}' y='28' font-size='22' text-anchor='middle' fill='#111827'>{{title}}</text>
<line x1='{{left-10}}' y1='{{height-bottom}}' x2='{{width-30}}' y2='{{height-bottom}}' stroke='#111827' stroke-width='2'/>
{{''.join(rects)}}
{{''.join(labels)}}
</svg>\"\"\"
    Path(path).write_text(svg, encoding="utf-8")

_write_generic_chart(figure_file, figure_title, numbers)
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
    "figure_titles": [figure_title] if numbers else [],
    "artifacts": ["result.json", "solver_notes.md", figure_file] if numbers else ["result.json", "solver_notes.md"],
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


def _task_type_text(context: dict[str, Any]) -> str:
    task_types = context.get("subproblem", {}).get("analysis", {}).get("task_types", [])
    return " ".join(str(item).lower() for item in task_types if str(item).strip())


def _forecast_solver_score(context: dict[str, Any]) -> float:
    task_text = _task_type_text(context)
    keywords = ("forecast", "predict", "time series", "fitting", "拟合", "预测")
    return 0.9 if any(keyword in task_text for keyword in keywords) else 0.0


def _optimization_solver_score(context: dict[str, Any]) -> float:
    task_text = _task_type_text(context)
    keywords = ("optimization", "decision", "optimize", "budget", "优化", "决策")
    return 0.9 if any(keyword in task_text for keyword in keywords) else 0.0


def _path_solver_score(context: dict[str, Any]) -> float:
    task_text = _task_type_text(context)
    keywords = ("path", "network", "route", "routing", "路径", "网络")
    return 0.9 if any(keyword in task_text for keyword in keywords) else 0.0


def _evaluation_solver_score(context: dict[str, Any]) -> float:
    task_text = _task_type_text(context)
    keywords = ("evaluation", "weight", "ranking", "evaluate", "评价", "权重")
    return 0.9 if any(keyword in task_text for keyword in keywords) else 0.0


def _geometry_solver_score(context: dict[str, Any]) -> float:
    return 1.2 if _looks_like_geometry_problem(context) else 0.0


def _generic_solver_score(context: dict[str, Any]) -> float:
    return 0.1


_FALLBACK_SOLVER_REGISTRY: SolverRegistry | None = None


def get_builtin_solver_registry() -> SolverRegistry:
    global _FALLBACK_SOLVER_REGISTRY
    if _FALLBACK_SOLVER_REGISTRY is None:
        registry = SolverRegistry()
        registry.register(
            SolverSpec(
                name="geometry_localization",
                matcher=_geometry_solver_score,
                builder=_build_geometry_solver_code,
                description="Geometry, localization, formation, and bearing-based problems.",
            )
        )
        registry.register(
            SolverSpec(
                name="forecast",
                matcher=_forecast_solver_score,
                builder=_build_forecast_solver_code,
                description="Forecasting and fitting problems.",
            )
        )
        registry.register(
            SolverSpec(
                name="optimization",
                matcher=_optimization_solver_score,
                builder=_build_optimization_solver_code,
                description="Optimization and decision problems.",
            )
        )
        registry.register(
            SolverSpec(
                name="path_network",
                matcher=_path_solver_score,
                builder=_build_path_solver_code,
                description="Path and network problems.",
            )
        )
        registry.register(
            SolverSpec(
                name="evaluation",
                matcher=_evaluation_solver_score,
                builder=_build_evaluation_solver_code,
                description="Evaluation and weighting problems.",
            )
        )
        registry.register(
            SolverSpec(
                name="generic",
                matcher=_generic_solver_score,
                builder=_build_generic_solver_code,
                description="Safe generic fallback for underspecified tasks.",
            )
        )
        _FALLBACK_SOLVER_REGISTRY = registry
    return _FALLBACK_SOLVER_REGISTRY


def build_fallback_solver_code(context: dict[str, Any]) -> tuple[str, str]:
    selection = get_builtin_solver_registry().select(context)
    if selection is None:
        return _build_generic_solver_code(context)
    return selection.summary, selection.code
