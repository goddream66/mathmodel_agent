from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ..state import SubProblem, TaskState
from ..tools import ToolRegistry


QUESTION_KEYWORDS = [
    "请",
    "求",
    "设计",
    "分析",
    "建立",
    "预测",
    "优化",
    "说明",
    "计算",
    "评估",
    "problem",
    "forecast",
    "predict",
    "optimize",
    "analyse",
    "analyze",
]


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _dedup(items: list[str], *, limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        clean = item.strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        output.append(clean)
        if limit is not None and len(output) >= limit:
            break
    return output


def _normalize_enum_label(label: str) -> str:
    digits = re.findall(r"\d+", label)
    if digits:
        return f"问题{int(digits[0])}"
    return "问题"


def _split_subproblems(problem_text: str) -> list[SubProblem]:
    text = problem_text.strip()
    if not text:
        return [SubProblem(title="问题", text="")]

    label_patterns = [
        r"问题\s*[一二三四五六七八九十百千万\d]+",
        r"第\s*[一二三四五六七八九十百千万\d]+\s*问",
        r"任务\s*[一二三四五六七八九十百千万\d]+",
        r"子问题\s*[一二三四五六七八九十百千万\d]+",
        r"Problem\s*\d+",
        r"Q\s*\d+",
    ]
    header_re = re.compile(rf"(?mi)^\s*(?P<label>{'|'.join(label_patterns)})\s*[:：、．.]?\s*")
    header_matches = list(header_re.finditer(text))
    if header_matches:
        subproblems: list[SubProblem] = []
        for index, match in enumerate(header_matches):
            start = match.end()
            end = header_matches[index + 1].start() if index + 1 < len(header_matches) else len(text)
            subproblems.append(SubProblem(title=match.group("label").strip(), text=text[start:end].strip()))
        return subproblems

    enum_re = re.compile(r"(?m)^\s*(?P<label>\(\d+\)|（\d+）|\d+\s*[.)、])\s*")
    enum_matches = list(enum_re.finditer(text))
    if len(enum_matches) >= 2:
        subproblems = []
        for index, match in enumerate(enum_matches):
            start = match.end()
            end = enum_matches[index + 1].start() if index + 1 < len(enum_matches) else len(text)
            subproblems.append(
                SubProblem(
                    title=_normalize_enum_label(match.group("label")),
                    text=text[start:end].strip(),
                )
            )
        return subproblems

    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n+", text) if paragraph.strip()]
    question_like = [paragraph for paragraph in paragraphs if _contains_any(paragraph, QUESTION_KEYWORDS)]
    if len(question_like) >= 2:
        return [
            SubProblem(title=f"子问题{i + 1}", text=paragraph)
            for i, paragraph in enumerate(question_like)
        ]

    return [SubProblem(title="问题", text=text)]


def _build_solution_plan(task_types: list[str]) -> list[str]:
    plan: list[str] = ["先明确输入、输出、约束和评价指标，避免模型目标漂移。"]

    if "预测/拟合" in task_types or "参数估计" in task_types:
        plan.extend(
            [
                "整理历史数据并检查缺失、异常值和单位一致性。",
                "先建立基线模型，再与更复杂模型做对比。",
                "使用误差指标和回测结果评估预测稳定性。",
            ]
        )

    if "优化/决策" in task_types:
        plan.extend(
            [
                "把文字规则转成决策变量、目标函数和约束条件。",
                "区分连续变量、整数变量和 0-1 变量。",
                "求解后做可行性检查和敏感性分析。",
            ]
        )

    if "路径/网络" in task_types:
        plan.extend(
            [
                "先抽象成图结构，明确节点、边和权重。",
                "根据目标选择最短路、最小费用流或车辆路径模型。",
                "验证容量、时间窗和路径连通性等业务约束。",
            ]
        )

    if "随机/仿真" in task_types:
        plan.extend(
            [
                "明确随机变量分布及参数来源。",
                "固定随机种子并进行多次仿真，统计均值和区间。",
                "通过敏感性分析说明模型稳定性。",
            ]
        )

    if "评价/权重" in task_types:
        plan.extend(
            [
                "建立指标体系并标明正向、逆向指标。",
                "选择 AHP、熵权或 TOPSIS 形成综合评价。",
                "检查权重稳定性和排序鲁棒性。",
            ]
        )

    if len(plan) == 1:
        plan.extend(["先给出一个可计算的基线模型。", "再做对比分析和结果解释。"])
    return _dedup(plan, limit=8)


def _infer_constraints(text: str, task_types: list[str]) -> list[str]:
    constraints: list[str] = []
    normalized = text.replace(" ", "")
    if _contains_any(normalized, ["约束", "限制", "不得", "必须", "至多", "至少", "不超过"]):
        constraints.append("题目文本中存在显式约束，需要转写为数学不等式或逻辑条件。")
    if "优化/决策" in task_types:
        constraints.append("需要明确资源上限、容量约束和业务规则。")
    if "路径/网络" in task_types:
        constraints.append("需要验证连通性、容量或时间窗约束。")
    if "预测/拟合" in task_types:
        constraints.append("训练与验证数据划分方式需要保持时序一致。")
    return _dedup(constraints, limit=5)


def _infer_assumptions(text: str, task_types: list[str]) -> list[str]:
    assumptions = [
        "变量定义清晰且可以被观测、估计或求解。",
        "原始题面没有说明的外部环境在分析周期内保持相对稳定。",
    ]
    if "预测/拟合" in task_types:
        assumptions.append("历史数据对未来具有一定代表性。")
    if "随机/仿真" in task_types:
        assumptions.append("随机过程的分布设定能够近似真实系统。")
    if "优化/决策" in task_types:
        assumptions.append("成本、收益或资源参数在求解区间内可视为已知。")
    if _contains_any(text, ["如果", "假设", "设定"]):
        assumptions.append("题面中的前置设定需要在模型部分显式列出。")
    return _dedup(assumptions, limit=6)


def _infer_objective(text: str, task_types: list[str]) -> str:
    if "优化/决策" in task_types:
        if _contains_any(text, ["最小", "最低", "减少"]):
            return "在满足约束的前提下最小化目标成本或风险。"
        if _contains_any(text, ["最大", "最高", "提升"]):
            return "在满足约束的前提下最大化收益、效率或覆盖率。"
        return "构建目标函数并求得最优决策方案。"
    if "预测/拟合" in task_types:
        return "建立预测模型并给出可解释的误差评估。"
    if "路径/网络" in task_types:
        return "在网络结构约束下找到最优路径或调度方案。"
    if "评价/权重" in task_types:
        return "构建评价体系并形成可信的排序结果。"
    if "随机/仿真" in task_types:
        return "通过仿真刻画系统行为并评估关键指标。"
    return "把题目转写成可计算、可解释、可验证的模型。"


def _infer_key_variables(task_types: list[str]) -> list[str]:
    variables: list[str] = []
    if "优化/决策" in task_types:
        variables.extend(["决策变量", "目标函数值", "约束边界"])
    if "预测/拟合" in task_types:
        variables.extend(["时间索引", "目标变量", "解释变量"])
    if "路径/网络" in task_types:
        variables.extend(["节点集合", "边权重", "路径选择变量"])
    if "评价/权重" in task_types:
        variables.extend(["指标值", "指标权重", "综合得分"])
    if "随机/仿真" in task_types:
        variables.extend(["随机变量", "仿真次数", "统计量"])
    if not variables:
        variables.append("核心状态变量")
    return _dedup(variables, limit=6)


def _infer_needed_data(task_types: list[str]) -> list[str]:
    needed_data: list[str] = []
    if "预测/拟合" in task_types:
        needed_data.extend(["历史观测数据", "外部影响因素或特征变量"])
    if "优化/决策" in task_types:
        needed_data.extend(["成本、收益或资源参数", "业务约束与上限"])
    if "路径/网络" in task_types:
        needed_data.extend(["节点和边信息", "距离、时间或费用矩阵"])
    if "评价/权重" in task_types:
        needed_data.extend(["指标明细数据", "指标方向说明"])
    if "随机/仿真" in task_types:
        needed_data.extend(["分布参数", "历史样本或经验规则"])
    if not needed_data:
        needed_data.append("题目中涉及的输入参数和边界条件")
    return _dedup(needed_data, limit=6)


def _infer_evaluation(task_types: list[str]) -> list[str]:
    evaluation: list[str] = ["检查假设是否合理、变量定义是否一致。"]
    if "预测/拟合" in task_types:
        evaluation.extend(["使用 MAE、RMSE、MAPE 等误差指标。", "进行回测或验证集评估。"])
    if "优化/决策" in task_types:
        evaluation.extend(["检查解的可行性和边界情况。", "做敏感性分析。"])
    if "路径/网络" in task_types:
        evaluation.append("比较总路径长度、总成本或准时率。")
    if "评价/权重" in task_types:
        evaluation.append("检查排序稳定性和权重鲁棒性。")
    if "随机/仿真" in task_types:
        evaluation.append("报告均值、方差和置信区间。")
    return _dedup(evaluation, limit=6)


def _infer_deliverables(task_types: list[str]) -> list[str]:
    deliverables = ["结构化建模思路", "关键公式或算法流程", "可复核的结论说明"]
    if "预测/拟合" in task_types:
        deliverables.append("预测结果与误差分析")
    if "优化/决策" in task_types:
        deliverables.append("最优方案与敏感性分析")
    if "路径/网络" in task_types:
        deliverables.append("路径或调度方案")
    if "评价/权重" in task_types:
        deliverables.append("评价排序与权重解释")
    if "随机/仿真" in task_types:
        deliverables.append("仿真统计结果")
    return _dedup(deliverables, limit=6)


def _infer_formulation_steps(task_types: list[str], objective: str, constraints: list[str]) -> list[str]:
    steps = [f"目标定义：{objective}"]
    if constraints:
        steps.append(f"约束梳理：{constraints[0]}")
    if "优化/决策" in task_types:
        steps.append("把目标与约束写成线性规划、整数规划或多目标优化模型。")
    if "预测/拟合" in task_types:
        steps.append("构建特征和时间索引，给出训练、验证和预测流程。")
    if "路径/网络" in task_types:
        steps.append("把问题映射到图模型并定义节点、边和权重。")
    if "评价/权重" in task_types:
        steps.append("先标准化指标，再进行赋权与综合评分。")
    if "随机/仿真" in task_types:
        steps.append("定义随机过程，再通过重复实验得到统计量。")
    return _dedup(steps, limit=6)


def _detect_task_types(text: str) -> list[str]:
    normalized = text.replace(" ", "")
    task_types: list[str] = []
    if _contains_any(normalized, ["预测", "预报", "趋势", "未来", "拟合", "时间序列", "forecast", "predict", "demand"]):
        task_types.append("预测/拟合")
    if _contains_any(normalized, ["最小", "最大", "优化", "约束", "成本", "收益", "利润", "预算", "调度", "选址", "分配", "optimize", "cost", "budget", "profit"]):
        task_types.append("优化/决策")
    if _contains_any(normalized, ["路径", "网络", "节点", "边", "运输", "配送", "最短路", "VRP", "route", "network", "path"]):
        task_types.append("路径/网络")
    if _contains_any(normalized, ["排队", "仿真", "蒙特卡洛", "随机", "概率", "simulation", "random", "montecarlo"]):
        task_types.append("随机/仿真")
    if _contains_any(normalized, ["评价", "权重", "排序", "指标体系", "综合评分", "evaluate", "weight", "ranking"]):
        task_types.append("评价/权重")
    if _contains_any(normalized, ["分类", "识别", "判别", "标签", "classify", "classification", "label"]):
        task_types.append("分类/判别")
    if _contains_any(normalized, ["聚类", "分群", "相似", "cluster", "clustering"]):
        task_types.append("聚类/分群")
    if _contains_any(normalized, ["参数估计", "最小二乘", "估计参数", "parameter", "leastsquares"]):
        task_types.append("参数估计")
    if not task_types:
        task_types.append("通用建模")
    return _dedup(task_types)


def _candidate_models_for(task_types: list[str]) -> list[str]:
    candidate_models: list[str] = []
    if "预测/拟合" in task_types:
        candidate_models.extend(["线性/非线性回归", "ARIMA/Prophet", "灰色预测 GM(1,1)"])
    if "优化/决策" in task_types:
        candidate_models.extend(["线性规划", "整数规划/混合整数规划", "多目标优化"])
    if "路径/网络" in task_types:
        candidate_models.extend(["最短路径模型", "最小费用流", "车辆路径问题"])
    if "随机/仿真" in task_types:
        candidate_models.extend(["蒙特卡洛仿真", "排队论", "离散事件仿真"])
    if "评价/权重" in task_types:
        candidate_models.extend(["AHP", "熵权法", "TOPSIS"])
    if "分类/判别" in task_types:
        candidate_models.extend(["逻辑回归", "支持向量机", "随机森林"])
    if "聚类/分群" in task_types:
        candidate_models.extend(["K-Means", "层次聚类", "DBSCAN"])
    if "参数估计" in task_types:
        candidate_models.extend(["最小二乘估计", "最大似然估计"])
    if not candidate_models:
        candidate_models.append("基线模型 + 对比实验")
    return _dedup(candidate_models, limit=6)


def _analyze(text: str) -> dict[str, Any]:
    task_types = _detect_task_types(text)
    candidate_models = _candidate_models_for(task_types)
    objective = _infer_objective(text, task_types)
    constraints = _infer_constraints(text, task_types)
    assumptions = _infer_assumptions(text, task_types)
    needed_data = _infer_needed_data(task_types)
    evaluation = _infer_evaluation(task_types)
    deliverables = _infer_deliverables(task_types)
    chosen_method = candidate_models[0] if candidate_models else None
    notes = [
        "先把题目里的变量、单位、边界条件统一。",
        "避免在没有数据支撑时直接给出数值结论。",
    ]
    if "通用建模" in task_types:
        notes.append("建议先做基线模型，再逐步增加复杂度。")

    return {
        "task_types": task_types,
        "candidate_models": candidate_models,
        "solution_plan": _build_solution_plan(task_types),
        "key_variables": _infer_key_variables(task_types),
        "needed_data": needed_data,
        "evaluation": evaluation,
        "notes": _dedup(notes, limit=5),
        "objective": objective,
        "constraints": constraints,
        "assumptions": assumptions,
        "deliverables": deliverables,
        "formulation_steps": _infer_formulation_steps(task_types, objective, constraints),
        "chosen_method": chosen_method,
        "confidence": 0.55 if "通用建模" in task_types else 0.75,
    }


@dataclass(frozen=True)
class ProblemDecomposeSkill:
    name: str = "decompose"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        state.subproblems = _split_subproblems(state.problem_text)
        return state


@dataclass(frozen=True)
class SubProblemAnalyzeSkill:
    name: str = "subproblem_analyze"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        if not state.subproblems:
            state.subproblems = _split_subproblems(state.problem_text)

        for subproblem in state.subproblems:
            analysis = _analyze(subproblem.text or subproblem.title)
            subproblem.analysis.task_types = analysis["task_types"]
            subproblem.analysis.candidate_models = analysis["candidate_models"]
            subproblem.analysis.solution_plan = analysis["solution_plan"]
            subproblem.analysis.key_variables = analysis["key_variables"]
            subproblem.analysis.needed_data = analysis["needed_data"]
            subproblem.analysis.evaluation = analysis["evaluation"]
            subproblem.analysis.notes = analysis["notes"]
            subproblem.analysis.objective = analysis["objective"]
            subproblem.analysis.constraints = analysis["constraints"]
            subproblem.analysis.assumptions = analysis["assumptions"]
            subproblem.analysis.deliverables = analysis["deliverables"]
            subproblem.analysis.formulation_steps = analysis["formulation_steps"]
            subproblem.analysis.chosen_method = analysis["chosen_method"]
            subproblem.analysis.confidence = analysis["confidence"]

        return state
