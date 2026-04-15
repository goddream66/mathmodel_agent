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

    def test_geometry_problem_uses_geometry_template(self) -> None:
        problem_text = (
            "Problem 1: locate the unknown point using 45 deg and 135 deg bearings "
            "from anchors at (0,0) and (10,0)."
        )
        state = Orchestrator(
            tools=ToolRegistry.with_defaults(out_dir="tests/template_outputs"),
        ).run(problem_text)

        self.assertEqual(len(state.solver_runs), 1)
        run = state.solver_runs[0]
        evidence = set(run.structured_result.get("evidence", []))
        self.assertIn("template_used=geometry_localization_template", evidence)
        numeric_results = run.structured_result.get("numeric_results", {})
        self.assertIn("estimated_x", numeric_results)
        self.assertIn("estimated_y", numeric_results)
        self.assertAlmostEqual(float(numeric_results["estimated_x"]), 5.0, delta=1.0)
        self.assertAlmostEqual(float(numeric_results["estimated_y"]), 5.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()
