import unittest

from mathagent.agents import ManagerAgent
from mathagent.orchestrator import Orchestrator, _EphemeralMemory
from mathagent.state import TaskState
from mathagent.tools import ToolRegistry


class WorkflowUpgradeTest(unittest.TestCase):
    def test_manager_runs_full_loop_with_default_tools(self) -> None:
        problem_text = "\n".join(
            [
                "问题1：请预测未来 7 天销量，并说明误差评估方法。",
                "问题2：在预算约束下最大化利润，并给出敏感性分析建议。",
            ]
        )
        state = Orchestrator(
            tools=ToolRegistry.with_defaults(out_dir="tests/workflow_outputs"),
        )
        state = state.run(problem_text)
        self.assertEqual(state.stage, "done")
        self.assertGreaterEqual(len(state.subproblems), 2)
        self.assertTrue(state.solver_runs)
        self.assertTrue(state.results.get("reviewed_solution"))
        self.assertTrue(state.results.get("final_review_done"))
        self.assertTrue(state.report_md)
        self.assertIn("# 求解与实验", state.report_md)

    def test_modeling_produces_richer_structure(self) -> None:
        state = ManagerAgent().modeling.run(
            TaskState(
                problem_text=(
                    "问题1：在成本约束下选择配送方案。\n"
                    "问题2：根据历史数据预测未来需求。"
                )
            ),
            tools=ToolRegistry.empty(),
            memory=_EphemeralMemory(),
        )
        self.assertTrue(state.subproblems)
        first = state.subproblems[0].analysis
        self.assertIsNotNone(first.objective)
        self.assertTrue(first.formulation_steps)
        self.assertTrue(first.assumptions)


if __name__ == "__main__":
    unittest.main()
