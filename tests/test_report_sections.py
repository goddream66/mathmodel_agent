import unittest

from mathagent.orchestrator import Orchestrator
from mathagent.reporting import resolve_report_sections, select_report_sections
from mathagent.tools import ToolRegistry


class ReportSectionsTest(unittest.TestCase):
    def test_select_report_sections_extracts_requested_blocks(self) -> None:
        state = Orchestrator(
            tools=ToolRegistry.with_defaults(out_dir="tests/report_outputs"),
        ).run("Problem 1: forecast demand for 3 days using values 5 7 9 11.")

        sections = resolve_report_sections(["abstract", "results"])
        report = select_report_sections(state.report_md or "", sections)

        self.assertIn("# 摘要", report)
        self.assertIn("# 结果与分析", report)
        self.assertNotIn("# 求解与实验", report)

    def test_resolve_report_sections_accepts_chinese_aliases(self) -> None:
        self.assertEqual(resolve_report_sections(["摘要", "结果"]), ["abstract", "results"])


if __name__ == "__main__":
    unittest.main()
