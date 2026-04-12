import json
import unittest
from unittest.mock import patch

from mathagent.llm.custom_http import CustomHTTPClient, _extract_path
from mathagent.llm.types import Message


class _FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class CustomHTTPClientTest(unittest.TestCase):
    def test_extract_path(self) -> None:
        data = {"choices": [{"message": {"content": "hello"}}]}
        self.assertEqual(_extract_path(data, "choices.0.message.content"), "hello")

    def test_chat_uses_custom_templates(self) -> None:
        client = CustomHTTPClient(
            base_url="https://relay.example.com",
            api_key="secret",
            model="relay-model",
            path="/chat",
            headers={"X-Relay-Key": "{api_key}"},
            body_template={
                "model": "{model}",
                "input": "$messages",
                "temp": "$temperature",
            },
            response_path="data.answer",
        )
        with patch("urllib.request.urlopen", return_value=_FakeResponse({"data": {"answer": "ok"}})):
            text = client.chat([Message(role="user", content="hi")], temperature=0.3)
        self.assertEqual(text, "ok")
