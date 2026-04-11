import unittest

from mathagent.orchestrator import Orchestrator
from mathagent.tools import ToolRegistry


class ProblemAnalysisTest(unittest.TestCase):
    def test_split_zh_questions(self) -> None:
        text = "\n".join(
            [
                "题目背景：……",
                "问题一：请预测未来7天销量。",
                "问题二：在预算约束下最大化利润。",
                "问题三：给出配送路线最短。",
            ]
        )
        state = Orchestrator(tools=ToolRegistry.empty()).run(text)
        self.assertGreaterEqual(len(state.subproblems), 3)
        titles = [sp.title for sp in state.subproblems[:3]]
        self.assertEqual(titles[0].replace("：", ""), "问题一")
        self.assertEqual(titles[1].replace("：", ""), "问题二")
        self.assertEqual(titles[2].replace("：", ""), "问题三")

    def test_split_numeric_enumeration(self) -> None:
        text = "\n".join(
            [
                "(1) 预测未来7天销量。",
                "(2) 在预算约束下最大化利润。",
                "(3) 给出配送路线最短。",
                "(4) 做敏感性分析并给出结论。",
            ]
        )
        state = Orchestrator(tools=ToolRegistry.empty()).run(text)
        self.assertGreaterEqual(len(state.subproblems), 4)
        titles = [sp.title for sp in state.subproblems[:4]]
        self.assertEqual(titles[0], "问题1")
        self.assertEqual(titles[1], "问题2")
        self.assertEqual(titles[2], "问题3")
        self.assertEqual(titles[3], "问题4")

    def test_keyword_model_suggestion(self) -> None:
        text = "\n".join(
            [
                "问题一：预测未来销量，并给出误差评价。",
                "问题二：在约束条件下最小化总成本。",
            ]
        )
        state = Orchestrator(tools=ToolRegistry.empty()).run(text)
        sp1 = state.subproblems[0]
        sp2 = state.subproblems[1]

        self.assertTrue(any("时间序列" in m or "回归" in m for m in sp1.analysis.candidate_models))
        self.assertTrue(any("规划" in m or "整数" in m for m in sp2.analysis.candidate_models))


if __name__ == "__main__":
    unittest.main()
