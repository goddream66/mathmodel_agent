import json
import unittest
from pathlib import Path

from mathagent.tools import PythonExecTool


class PythonExecToolTest(unittest.TestCase):
    def test_executes_code_and_collects_artifacts(self) -> None:
        tool = PythonExecTool(work_dir=Path("tests/tool_runs"))
        result = tool.run(
            {
                "code": (
                    "from pathlib import Path\n"
                    "import json\n"
                    "Path('summary.json').write_text(json.dumps({'ok': True}), encoding='utf-8')\n"
                    "print('done')\n"
                )
            }
        )
        self.assertTrue(result["success"])
        self.assertIn("done", result["stdout"])
        self.assertIn("summary.json", result["artifacts"])


if __name__ == "__main__":
    unittest.main()
