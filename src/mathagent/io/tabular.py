from __future__ import annotations

import re
from typing import Any


ROLE_ALIASES: dict[str, tuple[str, ...]] = {
    "time": (
        "time",
        "date",
        "day",
        "period",
        "week",
        "month",
        "year",
        "quarter",
        "timestamp",
        "ds",
        "t",
        "日期",
        "时间",
        "天",
        "周",
        "月",
        "年",
        "季度",
        "期数",
    ),
    "value": (
        "value",
        "values",
        "demand",
        "sale",
        "sales",
        "qty",
        "quantity",
        "amount",
        "output",
        "volume",
        "target",
        "observation",
        "observed",
        "actual",
        "y",
        "需求",
        "销量",
        "销售",
        "数量",
        "产量",
        "目标值",
        "观测值",
        "实际值",
    ),
    "cost": (
        "cost",
        "price",
        "expense",
        "spend",
        "budget",
        "fee",
        "投入",
        "成本",
        "费用",
        "价格",
        "预算",
    ),
    "profit": (
        "value",
        "profit",
        "revenue",
        "benefit",
        "return",
        "gain",
        "score",
        "收益",
        "利润",
        "收入",
        "效益",
        "得分",
    ),
    "source": (
        "source",
        "from",
        "start",
        "origin",
        "src",
        "u",
        "起点",
        "源点",
        "开始",
    ),
    "target": (
        "target",
        "to",
        "end",
        "destination",
        "dest",
        "dst",
        "v",
        "终点",
        "目的地",
        "汇点",
        "结束",
    ),
    "weight": (
        "weight",
        "distance",
        "cost",
        "length",
        "time",
        "duration",
        "mile",
        "miles",
        "里程",
        "距离",
        "路程",
        "耗时",
        "时长",
        "边权",
        "权重",
    ),
    "score": (
        "score",
        "metric",
        "index",
        "rating",
        "grade",
        "指标",
        "评分",
        "分数",
        "得分",
    ),
}

NUMERIC_PREFERRED_ROLES = {"value", "cost", "profit", "weight", "score", "time"}
TEXT_PREFERRED_ROLES = {"source", "target"}


def normalize_column_name(name: Any) -> str:
    text = str(name or "").strip().lower()
    text = re.sub(r"[\s\-/.:]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def is_numeric_cell(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def summarize_table(columns: list[str], rows: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_columns = {column: normalize_column_name(column) for column in columns}
    numeric_columns = [
        column
        for column in columns
        if any(is_numeric_cell(row.get(column)) for row in rows)
    ]
    text_columns = [
        column
        for column in columns
        if any(isinstance(row.get(column), str) and str(row.get(column)).strip() for row in rows)
    ]
    column_roles = infer_column_roles(columns, rows)
    return {
        "normalized_columns": normalized_columns,
        "numeric_columns": numeric_columns,
        "text_columns": text_columns,
        "column_roles": column_roles,
        "task_roles": {
            "forecast": {
                key: value
                for key, value in {
                    "time": column_roles.get("time"),
                    "value": column_roles.get("value"),
                }.items()
                if value
            },
            "optimization": {
                key: value
                for key, value in {
                    "cost": column_roles.get("cost"),
                    "value": column_roles.get("profit") or column_roles.get("value"),
                }.items()
                if value
            },
            "path": {
                key: value
                for key, value in {
                    "source": column_roles.get("source"),
                    "target": column_roles.get("target"),
                    "weight": column_roles.get("weight"),
                }.items()
                if value
            },
            "evaluation": {
                key: value
                for key, value in {
                    "weight": column_roles.get("weight"),
                    "score": column_roles.get("score") or column_roles.get("value"),
                }.items()
                if value
            },
        },
    }


def infer_column_roles(columns: list[str], rows: list[dict[str, Any]]) -> dict[str, str]:
    info = {
        column: {
            "normalized": normalize_column_name(column),
            "numeric_count": sum(1 for row in rows if is_numeric_cell(row.get(column))),
            "text_count": sum(
                1
                for row in rows
                if isinstance(row.get(column), str) and str(row.get(column)).strip()
            ),
        }
        for column in columns
    }
    matched: dict[str, str] = {}
    for role, aliases in ROLE_ALIASES.items():
        best_column = None
        best_score = 0
        for column in columns:
            score = _score_column_match(info[column]["normalized"], aliases)
            if score <= 0:
                continue
            numeric_count = int(info[column]["numeric_count"])
            text_count = int(info[column]["text_count"])
            if role in NUMERIC_PREFERRED_ROLES and numeric_count:
                score += 10
            if role in TEXT_PREFERRED_ROLES and text_count:
                score += 10
            if role in TEXT_PREFERRED_ROLES and numeric_count and not text_count:
                score -= 15
            if role in NUMERIC_PREFERRED_ROLES and not numeric_count:
                score -= 15
            if score > best_score:
                best_column = column
                best_score = score
        if best_column is not None and best_score >= 55:
            matched[role] = best_column
    return matched


def _score_column_match(normalized_name: str, aliases: tuple[str, ...]) -> int:
    if not normalized_name:
        return 0
    best_score = 0
    tokens = [token for token in normalized_name.split("_") if token]
    for alias in aliases:
        normalized_alias = normalize_column_name(alias)
        if not normalized_alias:
            continue
        score = 0
        if normalized_name == normalized_alias:
            score = 100
        elif normalized_alias in tokens:
            score = 85
        elif normalized_name.startswith(normalized_alias) or normalized_name.endswith(normalized_alias):
            score = 75
        elif normalized_alias in normalized_name:
            score = 65
        elif normalized_name in normalized_alias:
            score = 60
        if score > best_score:
            best_score = score
    return best_score
