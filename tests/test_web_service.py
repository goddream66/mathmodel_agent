import unittest
from pathlib import Path

from mathagent.web.service import WebSessionService


class WebSessionServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root_dir = Path("tests/web_outputs")
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.service = WebSessionService(root_dir=self.root_dir)
        self.session = self.service.create_session()

    def test_run_session_with_messages_and_sections(self) -> None:
        self.service.add_message(
            self.session["session_id"],
            "Problem 1: forecast demand for 3 days using values 5 7 9 11.",
        )
        self.service.set_report_sections(self.session["session_id"], ["abstract", "results"])
        payload = self.service.run_session(self.session["session_id"])

        self.assertTrue(payload["report_ready"])
        self.assertIn("# 摘要", payload["report"]["selected_report_md"])
        self.assertIn("# 结果与分析", payload["report"]["selected_report_md"])
        self.assertNotIn("# 求解与实验", payload["report"]["selected_report_md"])

    def test_upload_data_file_and_run(self) -> None:
        csv_path = Path("tests/fixtures/forecast_series.csv")
        self.service.add_message(
            self.session["session_id"],
            "Problem 1: forecast demand for the next 3 days.",
        )
        self.service.upload_files(
            self.session["session_id"],
            role="data",
            files=[(csv_path.name, csv_path.read_bytes())],
        )
        payload = self.service.run_session(self.session["session_id"])

        latest_state = payload["latest_state"]
        self.assertIsNotNone(latest_state)
        self.assertEqual(latest_state["solver_run_count"], 1)
        self.assertEqual(payload["data_files"][0]["name"], "forecast_series.csv")


if __name__ == "__main__":
    unittest.main()
