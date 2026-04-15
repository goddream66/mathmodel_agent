from __future__ import annotations
import json
import math
import re
from pathlib import Path

context = {
  "problem_text": "Problem 1: locate the unknown point using 45 deg and 135 deg bearings from anchors at (0,0) and (10,0).",
  "clarifications": [
    "Problem 1: what are the hard and soft constraints?"
  ],
  "subproblem_index": 1,
  "subproblem": {
    "title": "Problem 1",
    "text": "locate the unknown point using 45 deg and 135 deg bearings from anchors at (0,0) and (10,0).",
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
      "title": "Problem 1",
      "text": "locate the unknown point using 45 deg and 135 deg bearings from anchors at (0,0) and (10,0).",
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
  "input_data": {},
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
tables = [table for table in context.get("input_data", {}).get("tables", []) if table.get("kind") == "table"]
text = subproblem["text"] or context["problem_text"]

def _wrap_angle_deg(value):
    return (float(value) + 180.0) % 360.0 - 180.0

def _bearing_deg(ax, ay, px, py):
    return math.degrees(math.atan2(py - ay, px - ax))

def _coord_columns(columns):
    lower_map = {str(column).lower(): str(column) for column in columns}
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
            label = str(label).strip() if label not in {None, ""} else f"P{index}"
            points.append({"label": label, "x": float(x_value), "y": float(y_value)})
        if points:
            return table.get("name", "table"), points
    return None, []

def _extract_angle_rows():
    for table in tables:
        columns = list(table.get("columns", []))
        lower_map = {str(column).lower(): str(column) for column in columns}
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
                label = str(label).strip() if label not in {None, ""} else f"M{index}"
                rows.append(
                    {
                        "label": label,
                        "x": float(row[x_col]),
                        "y": float(row[y_col]),
                        "angle_deg": float(angle_value),
                    }
                )
        if rows:
            return table.get("name", "table"), rows
    return None, []

table_name, points = _extract_points_from_tables()
angle_table_name, angle_rows = _extract_angle_rows()
coord_pairs = [
    (float(x), float(y))
    for x, y in re.findall(r"\(([-+]?\d+(?:\.\d+)?),\s*([-+]?\d+(?:\.\d+)?)\)", text)
]
text_angles = [
    float(value)
    for value in re.findall(r"([-+]?\d+(?:\.\d+)?)\s*(?:deg|degree|degrees|°|度)", text, re.IGNORECASE)
]

if not points and coord_pairs:
    points = [{"label": f"P{index + 1}", "x": pair[0], "y": pair[1]} for index, pair in enumerate(coord_pairs)]

measurements = []
if angle_rows:
    measurements = list(angle_rows)
elif points and text_angles:
    usable = min(len(points), len(text_angles))
    measurements = [
        {
            "label": points[index]["label"],
            "x": points[index]["x"],
            "y": points[index]["y"],
            "angle_deg": float(text_angles[index]),
        }
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

figure_title = f"{subproblem['title']}: geometry layout and estimated position"
figure_file = "geometry_layout.svg"

def _write_layout(path):
    plot_points = [{"x": item["x"], "y": item["y"], "label": item["label"], "kind": "anchor"} for item in points]
    if estimated_x is not None and estimated_y is not None:
        plot_points.append({"x": estimated_x, "y": estimated_y, "label": "Estimated", "kind": "estimate"})
    elif formation_center_x is not None and formation_center_y is not None:
        plot_points.append({"x": formation_center_x, "y": formation_center_y, "label": "Center", "kind": "estimate"})
    if not plot_points:
        plot_points = [{"x": 0.0, "y": 0.0, "label": "N/A", "kind": "anchor"}]
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
        circles.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{radius}' fill='{fill}' />")
        labels.append(f"<text x='{x + 8:.1f}' y='{y - 8:.1f}' font-size='12' fill='#111827'>{item['label']}</text>")
    target_x = estimated_x if estimated_x is not None else formation_center_x
    target_y = estimated_y if estimated_y is not None else formation_center_y
    if target_x is not None and target_y is not None:
        tx, ty = _xy(target_x, target_y)
        for item in measurements:
            ax, ay = _xy(item["x"], item["y"])
            rays.append(f"<line x1='{ax:.1f}' y1='{ay:.1f}' x2='{tx:.1f}' y2='{ty:.1f}' stroke='#94a3b8' stroke-dasharray='6 4' />")
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>
<rect width='100%' height='100%' fill='white'/>
<text x='{width/2:.1f}' y='28' font-size='22' text-anchor='middle' fill='#111827'>{figure_title}</text>
<rect x='{left}' y='{top}' width='{plot_w}' height='{plot_h}' fill='#f8fafc' stroke='#cbd5e1'/>
{''.join(rays)}
{''.join(circles)}
{''.join(labels)}
</svg>"""
    Path(path).write_text(svg, encoding="utf-8")

_write_layout(figure_file)

numeric_results = {
    "point_count": len(points),
    "measurement_count": len(measurements),
}
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

result = {
    "subproblem_title": subproblem["title"],
    "status": status,
    "method": analysis.get("chosen_method") or "geometry_localization_template_solver",
    "objective": analysis.get("objective") or "Estimate a geometric target position or summarize the current formation.",
    "assumptions": analysis.get("assumptions") or ["Angles and coordinates are interpreted in a common 2D plane."],
    "constraints": analysis.get("constraints") or ["Additional geometric measurements may be required for a unique exact solution."],
    "result_summary": f"Generated a geometry-focused structured result using {solver_mode} with {library_used}.",
    "evidence": [
        "template_used=geometry_localization_template",
        f"solver_mode={solver_mode}",
        f"library_used={library_used}",
        f"point_count={len(points)}",
        f"measurement_count={len(measurements)}",
        f"table_name={table_name or angle_table_name or 'none'}",
    ],
    "numeric_results": numeric_results,
    "figure_titles": [figure_title],
    "artifacts": ["result.json", "geometry_summary.json", figure_file],
    "next_steps": [
        "Provide more anchor or angle measurements if a more stable localization result is required.",
        "Add explicit geometric constraints such as equal-distance or formation spacing for a stronger solver.",
    ],
}

Path("result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
Path("geometry_summary.json").write_text(
    json.dumps(
        {
            "points": points,
            "measurements": measurements,
            "estimated_x": estimated_x,
            "estimated_y": estimated_y,
            "mean_residual_deg": mean_residual_deg,
            "max_residual_deg": max_residual_deg,
            "formation_center_x": formation_center_x,
            "formation_center_y": formation_center_y,
            "formation_radius": formation_radius,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps(result, ensure_ascii=False))