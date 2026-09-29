"""Pytest mark integration against committed cassettes."""

from pathlib import Path

import pytest

from tapeagent.demo.simple_agent import run_agent

FIXTURE_CASSETTES = Path(__file__).resolve().parent / "fixtures" / "cassettes"


@pytest.mark.tape("weather_query", cassette_dir=FIXTURE_CASSETTES, mode="replay")
def test_tape_fixture_replays_weather(tape_session) -> None:
    answer = run_agent("What's the weather in Pune?", tape_session)
    assert "Pune" in answer or "tool output" in answer
