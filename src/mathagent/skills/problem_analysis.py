from __future__ import annotations

import re
from dataclasses import dataclass

from ..state import SubProblem, TaskState
from ..tools import ToolRegistry


def _split_subproblems(problem_text: str) -> list[SubProblem]:
    text = problem_text.strip()
    if not text:
        return [SubProblem(title="问题", text="")]

    label_patterns = [
        r"问题\s*[一二三四五六七八九十百千]+",
        r"第\s*[一二三四五六七八九十百千]+\s*问",
        r"问题\s*\d+",
        r"第\s*\d+\s*问",
        r"任务\s*[一二三四五六七八九十百千]+",
        r"任务\s*\d+",
        r"子问题\s*[一二三四五六七八九十百千]+",
        r"子问题\s*\d+",
        r"Q\s*\d+",
    ]
    header_re = re.compile(
        rf"(?m)^\s*(?P<label>{'|'.join(label_patterns)})\s*[:：]?\s*"
    )
    header_matches = list(header_re.finditer(text))
    if header_matches:
        subproblems: list[SubProblem] = []
        for i, m in enumerate(header_matches):
            title = m.group("label").strip()
            start = m.end()
            end = header_matches[i + 1].start() if i + 1 < len(header_matches) else len(text)
            block = text[start:end].strip()
            subproblems.append(SubProblem(title=title, text=block))
        return subproblems

    enum_re = re.compile(
        r"(?m)^\s*(?P<label>（\d+）|\(\d+\)|\d+\s*[\.、\)]|\d+）|[A-Za-z]\s*[\.\)])\s*"
    )
    enum_matches = list(enum_re.finditer(text))
    if len(enum_matches) >= 2:
        subproblems = []
        for i, m in enumerate(enum_matches):
            title = _normalize_enum_label(m.group("label"))
            start = m.end()
            end = enum_matches[i + 1].start() if i + 1 < len(enum_matches) else len(text)
            block = text[start:end].strip()
            subproblems.append(SubProblem(title=title, text=block))
        return subproblems

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    question_like: list[str] = []
    for p in paragraphs:
        if _contains_any(p, ["问题", "任务", "请", "求", "计算", "给出", "证明", "分析", "设计", "确定"]):
            question_like.append(p)
    if len(question_like) >= 2:
        return [
            SubProblem(title=f"子问题{i + 1}", text=p)
            for i, p in enumerate(question_like)
        ]

    return [SubProblem(title="问题", text=text)]


def _normalize_enum_label(label: str) -> str:
    s = label.strip()
    digits = re.findall(r"\d+", s)
    if digits:
        return f"问题{int(digits[0])}"
    letters = re.findall(r"[A-Za-z]", s)
    if letters:
        return f"问题{letters[0].upper()}"
    return "问题"


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(k in text for k in keywords)


def _build_solution_plan(task_types: list[str]) -> list[str]:
    plan: list[str] = []

    if "预测/拟合" in task_types or "参数估计/拟合" in task_types:
        plan.extend(
            [
                "整理数据（缺失/异常/单位），构造特征并划分训练-验证",
                "先做基线模型（线性回归/移动平均）作为对照",
                "选择候选模型（回归/时间序列/灰色预测）并调参",
                "用 MAE/RMSE/MAPE 做评价，输出预测结果与不确定性说明",
            ]
        )

    if "优化/决策" in task_types:
        plan.extend(
            [
                "把文字规则抽象成：决策变量、目标函数、约束条件",
                "判断变量类型（连续/整数/0-1）并写出 LP/MIP 形式",
                "调用求解器求最优解，检查可行性与边界情况",
                "做敏感性分析（关键参数扰动）并解释结论",
            ]
        )

    if "网络/路径" in task_types:
        plan.extend(
            [
                "把问题抽象为图（节点、边、权重：距离/时间/费用）",
                "根据目标选择算法（最短路/最小费用流/VRP）",
                "输出路线方案并核对约束（容量/时间窗等）",
            ]
        )

    if "随机/仿真" in task_types:
        plan.extend(
            [
                "明确随机变量与分布/参数来源（经验分布或理论假设）",
                "搭建仿真流程并固定随机种子，重复试验",
                "输出均值/方差/置信区间，并做稳健性分析",
            ]
        )

    if "评价/权重" in task_types:
        plan.extend(
            [
                "建立指标体系，标注正向/逆向并做标准化",
                "选择权重方法（AHP/熵权）并做一致性或稳定性检查",
                "用 TOPSIS/关联分析得到排序，解释关键指标影响",
            ]
        )

    if not plan:
        plan.extend(
            [
                "先把题目拆分成子任务并澄清输入/输出",
                "建立可计算的基线模型，再逐步增加复杂度",
                "用对比实验与可解释性分析支撑结论",
            ]
        )

    seen: set[str] = set()
    out: list[str] = []
    for x in plan:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _analyze(text: str) -> dict[str, list[str]]:
    t = text.replace(" ", "")

    task_types: list[str] = []
    candidate_models: list[str] = []
    solution_plan: list[str] = []
    key_variables: list[str] = []
    needed_data: list[str] = []
    evaluation: list[str] = []
    notes: list[str] = []

    if _contains_any(t, ["预测", "预报", "趋势", "未来", "时间序列", "下一期", "未来几天", "拟合"]):
        task_types.append("预测/拟合")
        candidate_models.extend(["回归（线性/岭回归/随机森林回归）", "时间序列（ARIMA/Prophet/状态空间）", "灰色预测（GM(1,1)）"])
        needed_data.extend(["历史观测数据（按时间排序）", "可能的影响因素（特征）"])
        evaluation.extend(["MAE/RMSE/MAPE", "训练-验证划分或交叉验证"])

    if _contains_any(t, ["分类", "识别", "判别", "是否", "属于", "标签"]):
        task_types.append("分类/判别")
        candidate_models.extend(["逻辑回归", "SVM", "随机森林/梯度提升树"])
        needed_data.extend(["带标签样本", "可解释的特征"])
        evaluation.extend(["准确率/召回率/F1", "混淆矩阵"])

    if _contains_any(t, ["聚类", "分群", "类别划分", "相似", "分组"]):
        task_types.append("聚类/分群")
        candidate_models.extend(["K-means", "层次聚类", "DBSCAN"])
        needed_data.extend(["样本特征矩阵", "特征标准化方案"])
        evaluation.extend(["轮廓系数", "类内/类间距离对比"])

    if _contains_any(t, ["最小", "最少", "最大", "最多", "优化", "目标函数", "约束", "成本", "收益", "利润", "资源", "容量", "预算", "排产", "调度", "分配", "选址"]):
        task_types.append("优化/决策")
        candidate_models.extend(["线性规划（LP）", "整数规划/混合整数规划（IP/MIP）", "多目标优化（加权/ε-约束）"])
        key_variables.extend(["决策变量（0-1/整数/连续）", "约束（资源/容量/逻辑）", "目标（成本/收益/时间）"])
        needed_data.extend(["成本/收益参数", "资源上限与需求", "业务规则（逻辑约束）"])
        evaluation.extend(["目标值对比", "可行性检查", "敏感性分析"])
        notes.extend(["先把文字规则写成变量、目标、约束", "若有离散选择一般需要整数规划"])

    if _contains_any(t, ["最短路", "路径", "路线", "网络", "节点", "边", "连通", "流量", "运输", "配送", "车辆路径", "VRP"]):
        task_types.append("网络/路径")
        candidate_models.extend(["最短路（Dijkstra/Floyd）", "最大流/最小费用流", "车辆路径问题（VRP：启发式/整数规划）"])
        needed_data.extend(["节点与边（距离/时间/费用）", "需求点与约束（容量/时间窗）"])
        evaluation.extend(["总距离/总成本", "约束满足情况"])
        notes.extend(["路径类问题通常要先抽象成图"])

    if _contains_any(t, ["排队", "到达率", "服务率", "等待时间", "仿真", "蒙特卡洛", "随机", "概率"]):
        task_types.append("随机/仿真")
        candidate_models.extend(["蒙特卡洛仿真", "排队论（M/M/1 等）", "离散事件仿真"])
        needed_data.extend(["分布假设或历史样本", "随机过程参数"])
        evaluation.extend(["置信区间", "重复实验与方差分析"])
        notes.extend(["需要固定随机种子保证可复现"])

    if _contains_any(t, ["相关", "影响因素", "权重", "评价", "综合评分", "排序", "优劣", "指标体系"]):
        task_types.append("评价/权重")
        candidate_models.extend(["AHP 层次分析法", "熵权法", "TOPSIS/灰色关联分析"])
        needed_data.extend(["指标数据表", "正向/逆向指标定义"])
        evaluation.extend(["排序稳定性（扰动/敏感性）", "一致性检验（AHP）"])

    if _contains_any(t, ["拟合", "曲线", "参数估计", "最小二乘", "估计参数"]):
        if "预测/拟合" not in task_types:
            task_types.append("参数估计/拟合")
        candidate_models.extend(["最小二乘拟合（OLS）", "非线性最小二乘", "最大似然估计（MLE）"])
        evaluation.extend(["残差分析", "拟合优度（R²）"])

    if not task_types:
        task_types.append("通用建模")
        candidate_models.extend(["先抽象变量-目标-约束（或输入-输出）", "基线模型 + 对比实验", "可解释性优先"])
        notes.extend(["题目未出现明显关键词时，先做变量定义与需求澄清"])
    solution_plan = _build_solution_plan(task_types)

    def _dedup(items: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for x in items:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return {
        "task_types": _dedup(task_types),
        "candidate_models": _dedup(candidate_models)[:6],
        "solution_plan": solution_plan[:10],
        "key_variables": _dedup(key_variables)[:8],
        "needed_data": _dedup(needed_data)[:8],
        "evaluation": _dedup(evaluation)[:8],
        "notes": _dedup(notes)[:8],
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

        for sp in state.subproblems:
            analysis = _analyze(sp.text if sp.text else sp.title)
            sp.analysis.task_types = analysis["task_types"]
            sp.analysis.candidate_models = analysis["candidate_models"]
            sp.analysis.solution_plan = analysis["solution_plan"]
            sp.analysis.key_variables = analysis["key_variables"]
            sp.analysis.needed_data = analysis["needed_data"]
            sp.analysis.evaluation = analysis["evaluation"]
            sp.analysis.notes = analysis["notes"]

        return state
