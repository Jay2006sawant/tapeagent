"""Record / replay integration tests."""

from pathlib import Path

from tapeagent.cassette import load_cassette
from tapeagent.demo.simple_agent import run_agent
from tapeagent.diff import compare_runs
from tapeagent.session import TapeMode, tape


def test_record_then_replay_weather(tmp_path: Path) -> None:
    cassette_dir = tmp_path / "cassettes"
    with tape("weather_query", cassette_dir=cassette_dir, mode=TapeMode.RECORD) as session:
        answer = run_agent("What's the weather in Pune?", session)

    assert "tool output" in answer.lower() or "answer" in answer.lower()

    with tape("weather_query", cassette_dir=cassette_dir, mode=TapeMode.REPLAY) as session:
        replayed = run_agent("What's the weather in Pune?", session)

    assert replayed == answer


def test_diff_detects_shortened_tool_sequence(tmp_path: Path) -> None:
    cassette_dir = tmp_path / "cassettes"
    with tape("policy_query", cassette_dir=cassette_dir, mode=TapeMode.RECORD) as session:
        run_agent("What is the hostel curfew?", session)

    cassette = load_cassette(cassette_dir / "policy_query.yaml")
    baseline = cassette.get_run("policy_query")
    assert baseline is not None

    truncated = baseline.model_copy(deep=True)
    truncated.interactions = baseline.interactions[:-1]

    diff = compare_runs(baseline, truncated)
    assert diff.ok is False
    assert diff.tool_sequence_changed or diff.interaction_mismatches
