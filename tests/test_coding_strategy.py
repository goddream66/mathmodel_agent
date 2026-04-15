import unittest

from mathagent.orchestrator import Orchestrator
from mathagent.tools import ToolRegistry


class CodingStrategyTest(unittest.TestCase):
    def test_coding_runs_once_per_subproblem_with_structured_results(self) -> None:
        problem_text = "\n".join(
            [
                "Problem 1: forecast demand for the next 7 days and report one numeric indicator.",
                "Problem 2: optimize cost under a budget of 100 and explain the chosen method.",
            ]
        )
        state = Orchestrator(
            tools=ToolRegistry.with_defaults(out_dir="tests/coding_outputs"),
        ).run(problem_text)

        self.assertEqual(len(state.subproblems), 2)
        self.assertEqual(len(state.solver_runs), 2)
        self.assertIn(state.results.get("status"), {"solved", "partially_solved"})
        self.assertEqual(len(state.results.get("structured_solver_results", [])), 2)

        for run in state.solver_runs:
            self.assertTrue(run.schema_valid)
            self.assertTrue(run.structured_result)
            self.assertEqual(run.structured_result["subproblem_title"], run.subproblem_title)
            self.assertIn(run.structured_result["status"], {"ok", "partial"})
            self.assertTrue(run.structured_result["method"])
            self.assertTrue(run.structured_result["result_summary"])
            self.assertTrue(run.structured_result["evidence"])
            self.assertIn("figure_titles", run.structured_result)
            self.assertTrue(run.structured_result["figure_titles"])
            self.assertIn("result.json", run.artifacts)
            self.assertTrue(any(name.endswith(".svg") for name in run.artifacts))


if __name__ == "__main__":
    unittest.main()
