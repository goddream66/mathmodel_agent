import json
import os
import unittest
from pathlib import Path

from mathagent.llm.config import load_llm_config


class LLMConfigTest(unittest.TestCase):
    def test_loads_from_json_file(self) -> None:
        path = Path("tests/fixtures/llm_config.json")
        cfg = load_llm_config("MODELING", config_path=path)
        self.assertIsNotNone(cfg)
        assert cfg is not None
        self.assertEqual(cfg.provider, "custom_http")
        self.assertEqual(cfg.base_url, "https://relay.example.com")
        self.assertEqual(cfg.options["path"], "/chat")

    def test_env_used_as_fallback(self) -> None:
        old = os.environ.get("WRITING_API_KEY")
        os.environ["WRITING_API_KEY"] = "env-key"
        try:
            cfg = load_llm_config("WRITING", config_path=Path("does-not-exist.json"))
            self.assertIsNotNone(cfg)
            assert cfg is not None
            self.assertEqual(cfg.api_key, "env-key")
        finally:
            if old is None:
                os.environ.pop("WRITING_API_KEY", None)
            else:
                os.environ["WRITING_API_KEY"] = old
