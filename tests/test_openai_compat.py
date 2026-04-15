from mathagent.llm.openai_compat import _build_chat_url


def test_openai_compat_builds_chat_url_from_root_base() -> None:
    assert _build_chat_url("https://api.openai.com") == "https://api.openai.com/v1/chat/completions"


def test_openai_compat_builds_chat_url_from_v1_base() -> None:
    assert (
        _build_chat_url("https://dashscope.aliyuncs.com/compatible-mode/v1")
        == "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    )


def test_openai_compat_keeps_full_chat_path() -> None:
    assert (
        _build_chat_url("https://relay.example.com/v1/chat/completions")
        == "https://relay.example.com/v1/chat/completions"
    )
