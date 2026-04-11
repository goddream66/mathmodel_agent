from __future__ import annotations

from dataclasses import dataclass

from ..state import TaskState
from ..tools import ToolRegistry


@dataclass(frozen=True)
class IntakeSkill:
    name: str = "intake"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        state.stage = "clarify"
        return state


@dataclass(frozen=True)
class ClarifySkill:
    name: str = "clarify"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        state.clarifications.extend(
            [
                "题目里的决策变量是什么？",
                "目标是什么（最小/最大/预测/分类）？",
                "有哪些硬约束与软约束？",
                "数据从哪里来、时间/空间尺度是什么？",
            ]
        )
        state.stage = "model"
        return state


@dataclass(frozen=True)
class ModelSkill:
    name: str = "model"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        state.model.method_candidates = [
            "回归/时间序列",
            "线性/整数规划",
            "图论（最短路/最大流/匹配）",
            "仿真/蒙特卡洛",
        ]
        state.model.assumptions = ["变量定义清晰且可观测/可计算", "约束可用数学表达"]
        state.stage = "solve"
        return state


@dataclass(frozen=True)
class SolveSkill:
    name: str = "solve"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        state.results["status"] = "scaffold_only"
        state.stage = "validate"
        return state


@dataclass(frozen=True)
class ValidateSkill:
    name: str = "validate"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        state.results["checks"] = [
            "变量/符号是否都定义",
            "目标函数与约束是否自洽",
            "结果是否可复现（随机种子/版本）",
        ]
        state.stage = "report"
        return state


@dataclass(frozen=True)
class ReportSkill:
    name: str = "report"

    def run(self, state: TaskState, tools: ToolRegistry) -> TaskState:
        per_problem: list[str] = []
        for sp in state.subproblems:
            per_problem.extend(
                [
                    f"## {sp.title}",
                    (sp.text.strip() if sp.text.strip() else "（题干未拆出正文）"),
                    "",
                    "### 任务类型",
                    "- " + "\n- ".join(sp.analysis.task_types) if sp.analysis.task_types else "- （待补充）",
                    "",
                    "### 可能使用的模型/算法",
                    "- "
                    + "\n- ".join(sp.analysis.candidate_models)
                    if sp.analysis.candidate_models
                    else "- （待补充）",
                    "",
                    "### 建议求解流程",
                    "- " + "\n- ".join(sp.analysis.solution_plan) if sp.analysis.solution_plan else "- （待补充）",
                    "",
                    "### 关键变量（建议先明确）",
                    "- " + "\n- ".join(sp.analysis.key_variables) if sp.analysis.key_variables else "- （待补充）",
                    "",
                    "### 需要的数据/参数",
                    "- " + "\n- ".join(sp.analysis.needed_data) if sp.analysis.needed_data else "- （待补充）",
                    "",
                    "### 评价与验证",
                    "- " + "\n- ".join(sp.analysis.evaluation) if sp.analysis.evaluation else "- （待补充）",
                    "",
                    "### 注意点",
                    "- " + "\n- ".join(sp.analysis.notes) if sp.analysis.notes else "- （待补充）",
                    "",
                ]
            )

        clarifications_block = (
            "- " + "\n- ".join(state.clarifications) if state.clarifications else "- （暂无）"
        )

        report_lines: list[str] = [
            "# 摘要",
            "（此处生成摘要）",
            "",
            "# 问题重述",
            state.problem_text.strip(),
            "",
            "# 分题分析与方法选择",
        ]
        if per_problem:
            report_lines.extend(per_problem)
        else:
            report_lines.append("（未识别到“问题一/问题二/第1问”等结构，按整题处理）")
            report_lines.append("")

        report_lines.extend(
            [
                "# 需要澄清的问题",
                clarifications_block,
                "",
                "# 模型假设与符号",
                "（此处列出假设、符号表）",
                "",
                "# 模型建立与求解",
                "（此处给出目标函数、约束与算法）",
                "",
                "# 结果与分析",
                "（此处放表格/图像与敏感性分析）",
                "",
                "# 结论与展望",
                "（此处总结优缺点与改进方向）",
            ]
        )

        state.report_md = "\n".join(report_lines)
        return state
