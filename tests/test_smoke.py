import unittest

from mathagent.agents import ManagerAgent
from mathagent.memory import MemoryStore
from mathagent.tools import ToolRegistry


class SmokeTest(unittest.TestCase):
    def test_run(self) -> None:
        manager = ManagerAgent()
        state = manager.run(
            "一个简单的示例题目", tools=ToolRegistry.empty(), memory=MemoryStore("data/test_smoke.db")
        )
        self.assertTrue(state.report_md)


if __name__ == "__main__":
    unittest.main()
