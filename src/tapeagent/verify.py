"""Run verification scenarios in replay mode (for CI and `tapeagent verify`)."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml

from tapeagent.session import TapeMode, tape


@dataclass(frozen=True)
class Scenario:
    name: str
    cassette_dir: Path
    entrypoint: str


def load_manifest(path: Path) -> list[Scenario]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    scenarios: list[Scenario] = []
    base = path.parent
    for item in data.get("scenarios", []):
        cassette_dir = Path(item["cassette_dir"])
        if not cassette_dir.is_absolute():
            cassette_dir = (base / cassette_dir).resolve()
        scenarios.append(
            Scenario(
                name=item["name"],
                cassette_dir=cassette_dir,
                entrypoint=item["entrypoint"],
            )
        )
    return scenarios


def _resolve_callable(entrypoint: str) -> Callable:
    module_name, _, attr = entrypoint.partition(":")
    if not attr:
        raise ValueError(f"entrypoint must be module:callable, got {entrypoint!r}")
    module = importlib.import_module(module_name)
    fn = getattr(module, attr)
    if not callable(fn):
        raise TypeError(f"{entrypoint} is not callable")
    return fn


def run_scenario(scenario: Scenario) -> str:
    fn = _resolve_callable(scenario.entrypoint)
    with tape(scenario.name, cassette_dir=scenario.cassette_dir, mode=TapeMode.REPLAY) as session:
        return fn(session)


def verify_manifest(path: Path) -> list[tuple[str, str | Exception]]:
    results: list[tuple[str, str | Exception]] = []
    for scenario in load_manifest(path):
        try:
            output = run_scenario(scenario)
            if not output or not str(output).strip():
                results.append((scenario.name, ValueError("empty output")))
            else:
                results.append((scenario.name, output))
        except Exception as exc:
            results.append((scenario.name, exc))
    return results
