"""TapeSession: record or replay interactions inside a test or agent."""

from __future__ import annotations

import os
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any, Generator, Iterator

from tapeagent.cassette import (
    AgentRun,
    Cassette,
    Interaction,
    InteractionKind,
    cassette_path,
    hash_interaction_request,
    load_cassette,
    save_cassette,
)


class TapeMode(str, Enum):
    RECORD = "record"
    REPLAY = "replay"
    AUTO = "auto"


def resolve_mode(requested: TapeMode, cassette_exists: bool) -> TapeMode:
    if requested == TapeMode.AUTO:
        env = os.environ.get("TAPEAGENT_MODE", "").lower()
        if env == "record":
            return TapeMode.RECORD
        if env == "replay":
            return TapeMode.REPLAY
        return TapeMode.REPLAY if cassette_exists else TapeMode.RECORD
    return requested


class TapeSession:
    """Records or replays LLM and tool interactions for one named run."""

    def __init__(
        self,
        run_name: str,
        cassette_file: Path,
        mode: TapeMode = TapeMode.AUTO,
        agent_id: str = "default",
    ) -> None:
        self.run_name = run_name
        self.cassette_file = cassette_file
        self.mode = mode
        self.agent_id = agent_id
        self._cassette: Cassette | None = None
        self._run: AgentRun | None = None
        self._replay_index = 0
        self._resolved_mode: TapeMode | None = None

    @property
    def is_recording(self) -> bool:
        return self._resolved_mode == TapeMode.RECORD

    @property
    def is_replaying(self) -> bool:
        return self._resolved_mode == TapeMode.REPLAY

    def __enter__(self) -> TapeSession:
        exists = self.cassette_file.exists()
        self._resolved_mode = resolve_mode(self.mode, exists)

        if self.cassette_file.exists():
            self._cassette = load_cassette(self.cassette_file)
        else:
            self._cassette = Cassette()

        if self.is_replaying:
            run = self._cassette.get_run(self.run_name) if self._cassette else None
            if run is None:
                raise FileNotFoundError(
                    f"No run {self.run_name!r} in cassette {self.cassette_file}"
                )
            self._run = run
            self._replay_index = 0
        else:
            self._run = AgentRun(name=self.run_name, agent_id=self.agent_id)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc is not None or self._run is None or self._cassette is None:
            return
        if self.is_recording:
            self._cassette.add_run(self._run)
            save_cassette(self.cassette_file, self._cassette)

    def record_llm(
        self,
        request: dict[str, Any],
        response: dict[str, Any],
        *,
        model: str = "llm",
    ) -> dict[str, Any]:
        if self._run is None:
            raise RuntimeError("TapeSession not started")

        if self.is_replaying:
            return self._next_replay(InteractionKind.LLM, model, request)

        interaction = Interaction(
            kind=InteractionKind.LLM,
            name=model,
            request=request,
            response=response,
        )
        self._run.interactions.append(interaction)
        return response

    def record_tool(
        self,
        name: str,
        request: dict[str, Any],
        result: Any,
        *,
        execute: bool | None = None,
    ) -> Any:
        """Record or replay a tool call.

        On replay, returns the cassette result unless ``execute=True`` (re-run tool, compare later).
        """
        if self._run is None:
            raise RuntimeError("TapeSession not started")

        if self.is_replaying:
            replayed = self._next_replay(
                InteractionKind.TOOL,
                name,
                request,
            )
            if execute:
                return result
            return replayed.get("result")

        response = {"result": result}
        interaction = Interaction(
            kind=InteractionKind.TOOL,
            name=name,
            request=request,
            response=response,
        )
        self._run.interactions.append(interaction)
        return result

    def _next_replay(
        self,
        kind: InteractionKind,
        name: str,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        if self._run is None:
            raise RuntimeError("No replay run loaded")

        if self._replay_index >= len(self._run.interactions):
            raise IndexError(
                f"Replay exhausted at step {self._replay_index}; agent took extra actions"
            )

        expected = self._run.interactions[self._replay_index]
        req_hash = hash_interaction_request(kind, name, request)

        if expected.kind != kind or expected.name != name:
            raise AssertionError(
                f"Step {self._replay_index}: expected {expected.kind.value}/{expected.name}, "
                f"got {kind.value}/{name}"
            )
        if expected.request_hash and req_hash != expected.request_hash:
            raise AssertionError(
                f"Step {self._replay_index}: request hash mismatch for {name}"
            )

        self._replay_index += 1
        return expected.response


@contextmanager
def tape(
    run_name: str,
    cassette_dir: Path | str = "cassettes",
    mode: TapeMode | str = TapeMode.AUTO,
    agent_id: str = "default",
) -> Generator[TapeSession, None, None]:
    if isinstance(mode, str):
        mode = TapeMode(mode)
    base = Path(cassette_dir)
    path = cassette_path(base, run_name)
    session = TapeSession(run_name, path, mode=mode, agent_id=agent_id)
    with session:
        yield session
