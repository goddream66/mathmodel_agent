import unittest

from mathagent.orchestrator import Orchestrator
from mathagent.reporting import required_report_titles
from mathagent.state import SolverRun, SubProblem, TaskState
from mathagent.tools import ToolRegistry
from mathagent.verification.checkers import (
    build_report_sources,
    build_verification_findings,
    build_verification_summary,
)


class VerificationSummaryTest(unittest.TestCase):
    def test_verification_summary_tracks_report_checks(self) -> None:
        state = Orchestrator(
            tools=ToolRegistry.with_defaults(out_dir="tests/verification_outputs"),
        ).run("Problem 1: forecast demand for 3 days using values 5 7 9 11.")

        summary = build_verification_summary(state)
        sources = build_report_sources(state)

        self.assertIn("report_checks", summary)
        self.assertIn("section_count", summary["report_checks"])
        self.assertIn("results", sources)
        self.assertIn("referenced_evidence_count", sources["results"])

    def test_verification_findings_flag_missing_sections_and_uncited_subproblems(self) -> None:
        state = Orchestrator(
            tools=ToolRegistry.with_defaults(out_dir="tests/verification_outputs"),
        ).run("Problem 1: forecast demand for 3 days using values 5 7 9 11.")

        state.report_md = required_report_titles()[0] + "\nOnly abstract content."
        summary = build_verification_summary(state)
        sources = build_report_sources(state)
        findings = build_verification_findings(state, summary, sources)

        messages = [item["message"] for item in findings]
        self.assertTrue(any("Missing required report section" in message for message in messages))
        self.assertTrue(any("does not consistently cite evidence" in message for message in messages))

    def test_verification_findings_escalate_results_without_evidence(self) -> None:
        subproblem = SubProblem(title="问题 1", text="给出一个结构化求解结果。")
        subproblem.analysis.objective = "输出一个结果。"
        subproblem.analysis.constraints = ["必须引用证据。"]
        subproblem.analysis.chosen_method = "示例方法"
        state = TaskState(
            problem_text="问题 1：给出一个结构化求解结果。",
            subproblems=[subproblem],
            solver_runs=[
                SolverRun(
                    subproblem_title="问题 1",
                    success=True,
                    summary="ok",
                    code="print('ok')",
                    schema_valid=True,
                    structured_result={
                        "subproblem_title": "问题 1",
                        "status": "ok",
                        "method": "demo",
                        "objective": "输出一个结果。",
                        "assumptions": ["示例假设"],
                        "constraints": ["必须引用证据。"],
                        "result_summary": "生成了结构化结果。",
                        "evidence": ["marker=demo"],
                        "numeric_results": {"score": 1},
                        "figure_titles": [],
                        "artifacts": ["result.json"],
                        "next_steps": [],
                    },
                )
            ],
            report_md="\n".join(
                [
                    "# 摘要",
                    "摘要内容。",
                    "",
                    "# 问题重述",
                    "问题重述。",
                    "",
                    "# 子问题分析与方法选择",
                    "## 问题 1",
                    "分析内容。",
                    "",
                    "# 模型假设与符号说明",
                    "建模内容。",
                    "",
                    "# 求解与实验",
                    "## 问题 1",
                    "- method: demo",
                    "",
                    "# 结果与分析",
                    "## 问题 1",
                    "这里只给出一个笼统结论，没有引用任何证据。",
                    "",
                    "# 结论与后续工作",
                    "结论。",
                ]
            ),
        )

        summary = build_verification_summary(state)
        sources = build_report_sources(state)
        findings = build_verification_findings(state, summary, sources)

        self.assertTrue(
            any(
                item["message"] == "The results section does not explicitly cite solver evidence markers."
                and item["severity"] == "high"
                for item in findings
            )
        )


if __name__ == "__main__":
    unittest.main()
