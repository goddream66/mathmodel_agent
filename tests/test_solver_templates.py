import unittest

from mathagent.orchestrator import Orchestrator
from mathagent.tools import ToolRegistry


class SolverTemplateTest(unittest.TestCase):
    def test_fallback_templates_vary_by_task_type(self) -> None:
        problem_text = "\n".join(
            [
                "Problem 1: forecast demand for the next 5 days using values 10 12 15 18 20.",
                "Problem 2: optimize cost under budget 100 with candidate costs 25 40 70.",
                "Problem 3: find a path with distances 9 4 7 3.",
                "Problem 4: evaluate alternatives with scores 80 76 91.",
            ]
        )
        state = Orchestrator(
            tools=ToolRegistry.with_defaults(out_dir="tests/template_outputs"),
        ).run(problem_text)

        evidence_sets = [set(run.structured_result.get("evidence", [])) for run in state.solver_runs]
        all_evidence = set().union(*evidence_sets)
        self.assertIn("template_used=baseline_forecast_template", all_evidence)
        self.assertIn("template_used=baseline_optimization_template", all_evidence)
        self.assertIn("template_used=baseline_path_template", all_evidence)
        self.assertIn("template_used=baseline_evaluation_template", all_evidence)
        self.assertTrue(any(item.startswith("library_used=") for item in all_evidence))


if __name__ == "__main__":
    unittest.main()
