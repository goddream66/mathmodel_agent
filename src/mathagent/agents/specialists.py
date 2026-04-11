from __future__ import annotations

from dataclasses import dataclass

from ..llm import Message, build_llm
from ..llm.config import load_llm_config
from ..llm.utils import extract_first_json
from ..memory import MemoryStore
from ..skills import (
    ClarifySkill,
    ModelSkill,
    ProblemDecomposeSkill,
    ReportSkill,
    SolveSkill,
    SubProblemAnalyzeSkill,
    ValidateSkill,
)
from ..state import SubProblem, TaskState
from ..tools import ToolRegistry


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
                            Message(
                                role="system",
                                content=(
                                    "你是数学建模竞赛的建模专家。你需要把题目拆成若干子问题，并对每个子问题输出结构化分析。"
                                    "你只输出 JSON（不要输出其它解释文字）。"
                                ),
                            ),
                            Message(
                                role="user",
                                content=(
                                    "题目全文如下：\n"
                                    f"{state.problem_text}\n\n"
                                    "请输出一个 JSON 数组，每个元素包含字段：\n"
                                    "- title: 子问题标题\n"
                                    "- task_types: string[]（例如 预测/优化/路径/仿真/评价）\n"
                                    "- candidate_models: string[]（该子问题候选模型/算法）\n"
                                    "- solution_plan: string[]（该子问题建议求解步骤）\n"
                                    "- key_variables: string[]（关键变量）\n"
                                    "- needed_data: string[]（需要的数据/参数）\n"
                                    "- evaluation: string[]（评价与验证方法）\n"
                                    "- notes: string[]（注意点）\n"
                                    "子问题数量不限。"
                                ),
                            ),
                        ],
                        temperature=0.2,
                    )
                )
                if isinstance(payload, list) and payload:
                    state.subproblems = []
                    for item in payload:
                        if not isinstance(item, dict):
                            continue
                        title = str(item.get("title") or "").strip() or "子问题"
                        text = str(item.get("text") or "").strip()
                        sp = SubProblem(title=title, text=text)
                        analysis = sp.analysis
                        analysis.task_types = list(item.get("task_types") or [])
                        analysis.candidate_models = list(item.get("candidate_models") or [])
                        analysis.solution_plan = list(item.get("solution_plan") or [])
                        analysis.key_variables = list(item.get("key_variables") or [])
                        analysis.needed_data = list(item.get("needed_data") or [])
                        analysis.evaluation = list(item.get("evaluation") or [])
                        analysis.notes = list(item.get("notes") or [])
                        state.subproblems.append(sp)
            except Exception:
                pass

        memory.set_shared("problem_text", state.problem_text)
        memory.set_shared_json(
            "subproblems",
            [
                {
                    "title": sp.title,
                    "text": sp.text,
                    "analysis": {
                        "task_types": sp.analysis.task_types,
                        "candidate_models": sp.analysis.candidate_models,
                        "solution_plan": sp.analysis.solution_plan,
                        "key_variables": sp.analysis.key_variables,
                        "needed_data": sp.analysis.needed_data,
                        "evaluation": sp.analysis.evaluation,
                        "notes": sp.analysis.notes,
                    },
                }
                for sp in state.subproblems
            ],
        )
        memory.set_agent_json(self.name, "clarifications", state.clarifications)
        memory.append_event("agent", self.name, "done", {"stage": state.stage})
        return state


@dataclass(frozen=True)
class CodingAgent:
    name: str = "coding"

    def run(self, state: TaskState, tools: ToolRegistry, memory: MemoryStore) -> TaskState:
        state = SolveSkill().run(state, tools)
        state = ValidateSkill().run(state, tools)
        memory.set_agent_json(self.name, "checks", state.results.get("checks", []))
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
                sub = [
                    {
                        "title": sp.title,
                        "analysis": {
                            "task_types": sp.analysis.task_types,
                            "candidate_models": sp.analysis.candidate_models,
                            "solution_plan": sp.analysis.solution_plan,
                            "key_variables": sp.analysis.key_variables,
                            "needed_data": sp.analysis.needed_data,
                            "evaluation": sp.analysis.evaluation,
                            "notes": sp.analysis.notes,
                        },
                    }
                    for sp in state.subproblems
                ]
                report = llm.chat(
                    [
                        Message(
                            role="system",
                            content=(
                                "你是数学建模竞赛论文写作专家。你要根据题面与分题分析，写一份结构完整、可直接提交的 Markdown 论文草稿。"
                                "保持措辞严谨、结构清晰。"
                            ),
                        ),
                        Message(
                            role="user",
                            content=(
                                "题目全文：\n"
                                f"{state.problem_text}\n\n"
                                "分题分析（JSON）：\n"
                                f"{sub}\n\n"
                                "请输出 Markdown，包含：摘要、问题重述、分题分析与方法选择、模型假设与符号、模型建立与求解、结果与分析、结论与展望。"
                                "分题分析要逐题写清楚每问用到的模型/算法与步骤。"
                            ),
                        ),
                    ],
                    temperature=0.2,
                )
                state.report_md = report.strip()
            except Exception:
                state = ReportSkill().run(state, tools)
        else:
            state = ReportSkill().run(state, tools)
        if state.report_md is not None:
            memory.set_shared("report_md", state.report_md)
        memory.append_event("agent", self.name, "done", {"stage": state.stage})
        return state
