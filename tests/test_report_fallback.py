import unittest

from mathagent.orchestrator import Orchestrator
from mathagent.tools import ToolRegistry


class ReportFallbackTest(unittest.TestCase):
    def test_report_mentions_numeric_results_and_evidence(self) -> None:
        state = Orchestrator(
            tools=ToolRegistry.with_defaults(out_dir="tests/report_outputs"),
        ).run("Problem 1: forecast demand for 3 days using values 5 7 9 11.")

        assert state.report_md is not None
        self.assertIn("Numeric Results", state.report_md)
        self.assertIn("Evidence", state.report_md)
        self.assertIn("forecast_value", state.report_md)
        self.assertIn("Figure Titles", state.report_md)
        self.assertIn("图表标题", state.report_md)


if __name__ == "__main__":
    unittest.main()
