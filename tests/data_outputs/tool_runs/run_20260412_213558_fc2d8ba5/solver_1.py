from __future__ import annotations
import json
import re
from pathlib import Path

context = {
  "problem_text": "Problem 1: find the best path through the network.",
  "clarifications": [
    "Which variables are the decision variables, state variables, and outputs?",
    "Which constraints must always hold?",
    "Which claims require quantitative evidence before they can appear in the final paper?"
  ],
  "subproblem_index": 1,
  "subproblem": {
    "title": "Problem 1",
    "text": "find the best path through the network.",
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
  "all_subproblems": [
    {
      "title": "Problem 1",
      "text": "find the best path through the network.",
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
    }
  ],
  "input_data": {
    "tables": [
      {
        "name": "path_edges",
        "source": "tests\\fixtures\\path_edges.csv",
        "kind": "table",
        "columns": [
          "source",
          "target",
          "distance"
        ],
        "rows": [
          {
            "source": "A",
            "target": "B",
            "distance": 4
          },
          {
            "source": "B",
            "target": "C",
            "distance": 6
          },
          {
            "source": "C",
            "target": "D",
            "distance": 3
          }
        ],
        "row_count": 3,
        "normalized_columns": {
          "source": "source",
          "target": "target",
          "distance": "distance"
        },
        "numeric_columns": [
          "distance"
        ],
        "text_columns": [
          "source",
          "target"
        ],
        "column_roles": {
          "time": "distance",
          "value": "target",
          "source": "source",
          "target": "target",
          "weight": "distance"
        },
        "task_roles": {
          "forecast": {
            "time": "distance",
            "value": "target"
          },
          "optimization": {
            "value": "target"
          },
          "path": {
            "source": "source",
            "target": "target",
            "weight": "distance"
          },
          "evaluation": {
            "weight": "distance",
            "score": "target"
          }
        }
      }
    ],
    "table_names": [
      "path_edges"
    ],
    "table_count": 1
  },
  "model": {
    "assumptions": [
      "变量定义清晰且可以被观测、估计或求解。",
      "原始题面没有说明的外部环境在分析周期内保持相对稳定。"
    ],
    "constraints": [
      "需要验证连通性、容量或时间窗约束。"
    ],
    "method_candidates": [
      "最短路径模型",
      "最小费用流",
      "车辆路径问题"
    ],
    "chosen_method": "最短路径模型",
    "formulation_outline": [
      "目标定义：在网络结构约束下找到最优路径或调度方案。",
      "约束梳理：需要验证连通性、容量或时间窗约束。",
      "把问题映射到图模型并定义节点、边和权重。"
    ],
    "evidence_gaps": [
      "节点和边信息",
      "距离、时间或费用矩阵"
    ]
  }
}
subproblem = context["subproblem"]
analysis = subproblem["analysis"]
tables = [table for table in context.get("input_data", {}).get("tables", []) if table.get("kind") == "table"]
text = subproblem["text"] or context["problem_text"]
numbers = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]
edge_count = max(len(numbers) - 1, 0)
library_used = "stdlib"
path_nodes = [f"N{i}" for i in range(len(numbers) + 1)] if numbers else []
table_name = None
source_column = None
target_column = None
weight_column = None
edge_rows = []
for table in tables:
    task_roles = table.get("task_roles", {}).get("path", {})
    source_column = task_roles.get("source") or table.get("column_roles", {}).get("source")
    target_column = task_roles.get("target") or table.get("column_roles", {}).get("target")
    weight_column = task_roles.get("weight") or table.get("column_roles", {}).get("weight")
    if not (source_column and target_column and weight_column):
        columns = list(table.get("columns", []))
        lower_map = {str(column).lower(): str(column) for column in columns}
        source_column = source_column or lower_map.get("source") or lower_map.get("from") or lower_map.get("start")
        target_column = target_column or lower_map.get("target") or lower_map.get("to") or lower_map.get("end")
        weight_column = weight_column or lower_map.get("weight") or lower_map.get("distance") or lower_map.get("cost")
    if source_column and target_column and weight_column:
        edge_rows = [
            row
            for row in table.get("rows", [])
            if row.get(source_column) not in {None, ""}
            and row.get(target_column) not in {None, ""}
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
result = {
    "subproblem_title": subproblem["title"],
    "status": status,
    "method": analysis.get("chosen_method") or "path_template_solver",
    "objective": analysis.get("objective") or "Produce a baseline path summary from detected weights.",
    "assumptions": analysis.get("assumptions") or ["Detected numbers are treated as rough edge weights."],
    "constraints": analysis.get("constraints") or ["The full graph structure is not explicitly available in the prompt context."],
    "result_summary": f"Generated a baseline path/network summary using {library_used}.",
    "evidence": [
        "template_used=baseline_path_template",
        f"library_used={library_used}",
        f"table_name={table_name or 'none'}",
        f"source_column={source_column or 'none'}",
        f"target_column={target_column or 'none'}",
        f"weight_column={weight_column or 'none'}",
        f"weight_count={len(numbers)}",
        f"edge_count_estimate={edge_count}",
        f"path_cost={path_cost}",
    ],
    "numeric_results": {
        "weight_count": len(numbers),
        "edge_count_estimate": edge_count,
        "path_cost": round(path_cost, 4),
        "node_count": len(path_nodes),
    },
    "artifacts": ["result.json", "path_summary.json"],
    "next_steps": [
        "Provide an explicit graph or distance matrix for exact shortest-path or routing calculations.",
        "Add capacity or time-window data if this is a VRP-style task.",
    ],
}
Path("result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
Path("path_summary.json").write_text(
    json.dumps(
        {
            "weights": numbers[:20],
            "edge_count_estimate": edge_count,
            "path_cost": path_cost,
            "shortest_path": shortest_path,
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print(json.dumps(result, ensure_ascii=False))