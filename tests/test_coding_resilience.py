import json
import unittest
from unittest.mock import patch

from mathagent.agents import specialists_v3 as spec
from mathagent.state import SubProblem, TaskState
from mathagent.tools import ToolRegistry


BAD_CODE = "items = []\nitems.append(value=1)\n"
FALLBACK_CODE = "print('fallback solver')\n"


class FakeLLM:
    def __init__(self, response: str) -> None:
        self._response = response

    def chat(self, messages, temperature: float = 0.0) -> str:  # noqa: ANN001
        return self._response


class FakePythonExecTool:
    name = "python_exec"
    description = "Fake python execution tool for tests"

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def run(self, input: dict) -> dict:  # noqa: A002
        self.calls.append(input)

        if input["code"] == FALLBACK_CODE:
            payload = {
                "subproblem_title": "Problem 1",
                "status": "ok",
                "method": "fallback_method",
                "objective": "Produce a stable structured result.",
                "assumptions": ["Fallback template is allowed."],
                "constraints": ["Use template output when generated code fails."],
                "result_summary": "Recovered with fallback solver.",
                "evidence": [],
                "numeric_results": {"score": 1},
                "figure_titles": ["Recovered Figure"],
                "artifacts": ["result.json"],
                "next_steps": ["Replace fallback solver with domain logic."],
            }
            return {
                "success": True,
                "run_dir": "",
                "artifacts": [],
                "stdout": json.dumps(payload, ensure_ascii=False),
                "stderr": "",
            }

        return {
            "success": False,
            "run_dir": "",
            "artifacts": [],
            "stdout": "",
            "stderr": "TypeError: list.append() takes no keyword arguments",
        }


class DummyMemory:
    def set_shared(self, key: str, value: str) -> None:  # noqa: ARG002
        return None

    def set_shared_json(self, key: str, value) -> None:  # noqa: ANN001, ARG002
        return None

    def set_agent(self, agent: str, key: str, value: str) -> None:  # noqa: ARG002
        return None

    def set_agent_json(self, agent: str, key: str, value) -> None:  # noqa: ANN001, ARG002
        return None

    def append_event(self, scope: str, agent: str, type: str, payload) -> None:  # noqa: ANN001, A003, ARG002
        return None


def _build_state() -> TaskState:
    subproblem = SubProblem(title="Problem 1", text="Forecast demand from numeric clues 10 12 13 16.")
    subproblem.analysis.chosen_method = "time_series"
    subproblem.analysis.objective = "Estimate the next value."
    subproblem.analysis.assumptions = ["Data trend is smooth."]
    subproblem.analysis.constraints = ["Only baseline data is available."]
    return TaskState(problem_text=subproblem.text, subproblems=[subproblem], stage="solve")


class CodingResilienceTest(unittest.TestCase):
    def test_validate_result_schema_synthesizes_evidence(self) -> None:
        payload = {
            "subproblem_title": "Problem 1",
            "status": "ok",
            "method": "demo_method",
            "objective": "Return structured results.",
            "assumptions": ["Assume baseline inputs are valid."],
            "constraints": ["Keep the schema stable."],
            "result_summary": "Structured results were generated.",
            "evidence": [],
            "numeric_results": {"rmse": 0.5},
            "figure_titles": ["Figure 1"],
            "artifacts": ["result.json", "chart.svg"],
            "next_steps": ["Add stronger validation."],
        }

        valid, normalized, error = spec._validate_result_schema(payload, "Problem 1")

        self.assertTrue(valid, error)
        self.assertTrue(normalized["evidence"])
        self.assertIn("auto_evidence=synthesized_from_available_outputs", normalized["evidence"])
        self.assertIn("numeric_result_keys=rmse", normalized["evidence"])

    def test_build_llm_solver_falls_back_when_generated_code_is_invalid(self) -> None:
        state = _build_state()
        subproblem = state.subproblems[0]
        llm_response = json.dumps(
            {
                "summary": "Generated invalid code.",
                "code": "```python\nif True print('broken')\n```",
            },
            ensure_ascii=False,
        )

        with (
            patch.object(spec, "load_llm_config", return_value=object()),
            patch.object(spec, "build_llm", return_value=FakeLLM(llm_response)),
            patch.object(spec, "render_prompt", return_value="prompt"),
        ):
            summary, code = spec._build_llm_solver(state, subproblem, 1)

        self.assertIn("Fallback was used because generated code had invalid syntax", summary)
        self.assertIn("template_used=", code)
        self.assertNotIn("if True print('broken')", code)

    def test_coding_agent_retries_with_fallback_after_runtime_error(self) -> None:
        state = _build_state()
        tool = FakePythonExecTool()
        tools = ToolRegistry.empty()
        tools.register(tool)
        memory = DummyMemory()

        with (
            patch.object(spec, "_build_llm_solver", return_value=("Generated solver.", BAD_CODE)),
            patch.object(spec, "_build_fallback_solver_code", return_value=("Fallback solver.", FALLBACK_CODE)),
            patch.object(spec.SolveSkill, "run", lambda self, state, tools: state),
        ):
            updated = spec.CodingAgent().run(state, tools, memory)

        self.assertEqual(len(tool.calls), 2)
        self.assertEqual(tool.calls[1]["filename"], "solver_1_fallback.py")
        self.assertEqual(updated.results["status"], "solved")
        self.assertEqual(updated.solver_runs[0].code, FALLBACK_CODE)
        self.assertTrue(updated.solver_runs[0].schema_valid)
        self.assertTrue(updated.solver_runs[0].success)
        self.assertIn("auto_evidence=synthesized_from_available_outputs", updated.solver_runs[0].structured_result["evidence"])


if __name__ == "__main__":
    unittest.main()
