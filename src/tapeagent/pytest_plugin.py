"""Pytest integration: fixtures and @pytest.mark.tape."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Generator

import pytest

from tapeagent.session import TapeMode, TapeSession, tape

DEFAULT_CASSETTE_ROOT = Path.cwd() / "cassettes"


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("tapeagent")
    group.addoption(
        "--tape-mode",
        choices=["auto", "record", "replay"],
        default=None,
        help="Override TAPEAGENT_MODE for tape fixtures",
    )
    group.addoption(
        "--tape-cassette-dir",
        default=None,
        help="Default directory for @pytest.mark.tape cassettes",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "tape(run_name, cassette_dir=None): run test inside a TapeSession",
    )
    mode_opt = config.getoption("--tape-mode")
    if mode_opt:
        import os

        os.environ["TAPEAGENT_MODE"] = mode_opt


@pytest.fixture
def tape_cassette_dir(request: pytest.FixtureRequest) -> Path:
    opt = request.config.getoption("--tape-cassette-dir")
    if opt:
        return Path(opt)
    if hasattr(request, "param") and request.param:
        return Path(request.param)
    return DEFAULT_CASSETTE_ROOT


@pytest.fixture
def tape_session(request: pytest.FixtureRequest, tape_cassette_dir: Path) -> Generator[TapeSession, None, None]:
    marker = request.node.get_closest_marker("tape")
    if marker is None:
        pytest.skip("use @pytest.mark.tape('run_name') or request tape_session with mark")

    run_name: str = marker.args[0]
    cassette_dir = marker.kwargs.get("cassette_dir", tape_cassette_dir)
    mode = marker.kwargs.get("mode", TapeMode.AUTO)
    if isinstance(mode, str):
        mode = TapeMode(mode)

    with tape(run_name, cassette_dir=Path(cassette_dir), mode=mode) as session:
        yield session


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """In replay mode, tag tape-marked tests for clarity in CI output."""
    import os

    if os.environ.get("TAPEAGENT_MODE", "").lower() != "replay":
        return
    for item in items:
        if item.get_closest_marker("tape"):
            item.add_marker(pytest.mark.filterwarnings("ignore::DeprecationWarning"))
