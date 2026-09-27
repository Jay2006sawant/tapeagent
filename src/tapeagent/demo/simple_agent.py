"""Minimal tool-using agent for demos, tests, and `tapeagent verify`."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TYPE_CHECKING

from tapeagent.llm import TapedLLM
from tapeagent.session import TapeMode, tape

if TYPE_CHECKING:
    from tapeagent.session import TapeSession

TOOLS: dict[str, Any] = {
    "get_weather": lambda city: {"city": city, "temp_c": 32, "condition": "haze"},
    "search_docs": lambda q: {"hits": [f"Policy excerpt for: {q}"]},
}

PACKAGE_CASSETTE_DIR = Path(__file__).resolve().parent / "cassettes"
DEFAULT_CASSETTE_DIR = PACKAGE_CASSETTE_DIR


def fake_llm(messages: list[dict[str, Any]], *, model: str = "mock", **_: Any) -> dict[str, Any]:
    """Deterministic mock: tool call on step 0, final answer on step 1."""
    user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    tool_calls = [m for m in messages if m.get("role") == "tool"]
    step = len(tool_calls)

    if step == 0 and "weather" in user.lower():
        return {
            "content": "",
            "tool_calls": [{"name": "get_weather", "arguments": {"city": "Pune"}}],
        }
    if step == 0:
        return {
            "content": "",
            "tool_calls": [{"name": "search_docs", "arguments": {"q": user[:80]}}],
        }
    last_tool = messages[-1].get("content", "")
    return {"content": f"Here is your answer based on tool output: {last_tool}"}


def run_agent(user_message: str, session: TapeSession) -> str:
    llm = TapedLLM(session, fake_llm)
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]

    for _ in range(5):
        out = llm.complete(messages)
        if out.get("tool_calls"):
            for tc in out["tool_calls"]:
                name = tc["name"]
                args = tc.get("arguments", {})
                fn = TOOLS[name]
                result = session.record_tool(name, args, fn(**args))
                messages.append(
                    {"role": "assistant", "content": "", "tool_calls": out["tool_calls"]}
                )
                messages.append({"role": "tool", "content": str(result), "name": name})
            continue
        return str(out.get("content", ""))

    return "max steps exceeded"


def run_weather_scenario(session: TapeSession | None = None) -> str:
    if session is not None:
        return run_agent("What's the weather in Pune?", session)
    with tape("weather_query", cassette_dir=DEFAULT_CASSETTE_DIR, mode=TapeMode.AUTO) as s:
        return run_agent("What's the weather in Pune?", s)


def run_policy_scenario(session: TapeSession | None = None) -> str:
    if session is not None:
        return run_agent("What is the hostel curfew?", session)
    with tape("policy_query", cassette_dir=DEFAULT_CASSETTE_DIR, mode=TapeMode.AUTO) as s:
        return run_agent("What is the hostel curfew?", s)
