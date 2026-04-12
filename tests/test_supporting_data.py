import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from mathagent.io import load_supporting_data
from mathagent.orchestrator import Orchestrator
from mathagent.tools import ToolRegistry


class SupportingDataTest(unittest.TestCase):
    def test_load_supporting_data_csv(self) -> None:
        data = load_supporting_data([Path("tests/fixtures/forecast_series.csv")])
        self.assertEqual(data["table_count"], 1)
        table = data["tables"][0]
        self.assertEqual(table["name"], "forecast_series")
        self.assertEqual(table["columns"], ["day", "demand"])
        self.assertEqual(table["row_count"], 5)
        self.assertEqual(table["task_roles"]["forecast"]["value"], "demand")

    def test_forecast_solver_prefers_table_data(self) -> None:
        input_data = load_supporting_data([Path("tests/fixtures/forecast_series.csv")])
        state = Orchestrator(
            tools=ToolRegistry.with_defaults(out_dir="tests/data_outputs"),
        ).run(
            "Problem 1: forecast demand for the next 3 days.",
            input_data=input_data,
        )
        result = state.solver_runs[0].structured_result
        self.assertEqual(result["numeric_results"]["historical_point_count"], 5)
        self.assertIn("table_name=forecast_series", result["evidence"])

    def test_forecast_solver_uses_alias_mapping(self) -> None:
        input_data = load_supporting_data([Path("tests/fixtures/forecast_alias_series.csv")])
        state = Orchestrator(
            tools=ToolRegistry.with_defaults(out_dir="tests/data_outputs"),
        ).run(
            "Problem 1: forecast demand for the next 2 days.",
            input_data=input_data,
        )
        result = state.solver_runs[0].structured_result
        self.assertIn("selected_column=qty_sold", result["evidence"])

    def test_optimization_solver_reads_cost_value_columns(self) -> None:
        input_data = load_supporting_data([Path("tests/fixtures/optimization_items.csv")])
        state = Orchestrator(
            tools=ToolRegistry.with_defaults(out_dir="tests/data_outputs"),
        ).run(
            "Problem 1: optimize profit under budget 100.",
            input_data=input_data,
        )
        result = state.solver_runs[0].structured_result
        self.assertIn("cost_column=cost", result["evidence"])
        self.assertIn("value_column=value", result["evidence"])
        self.assertGreaterEqual(float(result["numeric_results"]["selected_value"]), 0.0)

    def test_path_solver_reads_edge_table(self) -> None:
        input_data = load_supporting_data([Path("tests/fixtures/path_edges.csv")])
        state = Orchestrator(
            tools=ToolRegistry.with_defaults(out_dir="tests/data_outputs"),
        ).run(
            "Problem 1: find the best path through the network.",
            input_data=input_data,
        )
        result = state.solver_runs[0].structured_result
        self.assertIn("table_name=path_edges", result["evidence"])
        self.assertIn("source_column=source", result["evidence"])
        self.assertIn("target_column=target", result["evidence"])
        self.assertIn("weight_column=distance", result["evidence"])

    def test_path_solver_uses_alias_mapping(self) -> None:
        input_data = load_supporting_data([Path("tests/fixtures/path_alias_edges.csv")])
        state = Orchestrator(
            tools=ToolRegistry.with_defaults(out_dir="tests/data_outputs"),
        ).run(
            "Problem 1: find the best path through the network.",
            input_data=input_data,
        )
        result = state.solver_runs[0].structured_result
        self.assertIn("source_column=from_node", result["evidence"])
        self.assertIn("target_column=to_node", result["evidence"])
        self.assertIn("weight_column=travel_cost", result["evidence"])

    def test_load_supporting_data_xlsx_with_mocked_openpyxl(self) -> None:
        class FakeWorksheet:
            title = "Sheet1"

            def iter_rows(self, values_only: bool = True):
                yield ("period", "qty_sold")
                yield (1, 10)
                yield (2, 13)

        class FakeWorkbook:
            worksheets = [FakeWorksheet()]

            def close(self) -> None:
                return None

        fake_module = SimpleNamespace(load_workbook=lambda **kwargs: FakeWorkbook())
        workbook_path = Path("tests/data_outputs/mock_workbook.xlsx")
        with mock.patch.dict("sys.modules", {"openpyxl": fake_module}):
            data = load_supporting_data([workbook_path])

        self.assertEqual(data["table_count"], 1)
        table = data["tables"][0]
        self.assertEqual(table["columns"], ["period", "qty_sold"])
        self.assertEqual(table["task_roles"]["forecast"]["value"], "qty_sold")


if __name__ == "__main__":
    unittest.main()
