import unittest
from pathlib import Path

from mathagent.memory import MemoryStore


class MemoryStoreTest(unittest.TestCase):
    def test_shared_and_agent_isolation(self) -> None:
        db_path = Path("data/test_memory.db")
        store = MemoryStore(db_path)

        store.set_shared("k", "v_shared")
        store.set_agent("a", "k", "v_a")
        store.set_agent("b", "k", "v_b")

        self.assertEqual(store.get_shared("k"), "v_shared")
        self.assertEqual(store.get_agent("a", "k"), "v_a")
        self.assertEqual(store.get_agent("b", "k"), "v_b")
        self.assertIsNone(store.get_agent("c", "k"))


if __name__ == "__main__":
    unittest.main()

