from pathlib import Path

from tapeagent.verify import load_manifest, run_scenario


def test_manifest_loads() -> None:
    manifest = Path(__file__).resolve().parents[1] / "examples" / "verify_manifest.yaml"
    scenarios = load_manifest(manifest)
    assert len(scenarios) >= 2
    names = {s.name for s in scenarios}
    assert "weather_query" in names
    assert "policy_query" in names


def test_replay_committed_cassettes() -> None:
    manifest = Path(__file__).resolve().parents[1] / "examples" / "verify_manifest.yaml"
    for scenario in load_manifest(manifest):
        out = run_scenario(scenario)
        assert isinstance(out, str) and len(out) > 10
