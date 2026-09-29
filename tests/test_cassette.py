from pathlib import Path

from tapeagent.cassette import AgentRun, Cassette, Interaction, InteractionKind, load_cassette, save_cassette


def test_roundtrip_cassette(tmp_path: Path) -> None:
    path = tmp_path / "demo.yaml"
    run = AgentRun(
        name="test_one",
        interactions=[
            Interaction(
                kind=InteractionKind.TOOL,
                name="ping",
                request={"x": 1},
                response={"result": "pong"},
            )
        ],
    )
    cassette = Cassette(runs={"test_one": run})
    save_cassette(path, cassette)
    loaded = load_cassette(path)
    assert loaded.get_run("test_one") is not None
    assert loaded.get_run("test_one").tool_sequence == ["ping"]
