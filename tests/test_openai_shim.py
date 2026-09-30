from pathlib import Path
from types import SimpleNamespace

from tapeagent.openai_shim import TapedOpenAI, _flatten_openai_completion
from tapeagent.session import TapeMode, tape


class FakeCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        message = SimpleNamespace(content="hello", tool_calls=[])
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice], model_dump=lambda: {"choices": [{"message": {"content": "hello"}}]})


class FakeClient:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions())


def test_record_replay_openai_shim(tmp_path: Path) -> None:
    cassette_dir = tmp_path / "cassettes"
    client = FakeClient()

    with tape("openai_once", cassette_dir=cassette_dir, mode=TapeMode.RECORD) as session:
        wrapped = TapedOpenAI(session, client)
        resp = wrapped.chat.completions.create(model="gpt-test", messages=[{"role": "user", "content": "hi"}])
        assert client.chat.completions.calls == 1
        assert resp.choices[0].message.content == "hello"

    client2 = FakeClient()
    with tape("openai_once", cassette_dir=cassette_dir, mode=TapeMode.REPLAY) as session:
        wrapped = TapedOpenAI(session, client2)
        resp = wrapped.chat.completions.create(model="gpt-test", messages=[{"role": "user", "content": "hi"}])
        assert client2.chat.completions.calls == 0
        assert resp["content"] == "hello"


def test_flatten_stores_tool_calls() -> None:
    flat = _flatten_openai_completion(
        {"choices": [{"message": {"content": "x", "tool_calls": [{"id": "1"}]}}]}
    )
    assert flat["content"] == "x"
    assert len(flat["tool_calls"]) == 1
