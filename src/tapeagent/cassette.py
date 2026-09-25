"""Cassette schema: ordered interactions that define one agent run."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class InteractionKind(str, Enum):
    LLM = "llm"
    TOOL = "tool"


class Interaction(BaseModel):
    """One step in an agent run — either an LLM round-trip or a tool invocation."""

    kind: InteractionKind
    name: str = Field(description="Tool name for tools; model id or 'llm' for LLM calls.")
    request: dict[str, Any] = Field(default_factory=dict)
    response: dict[str, Any] = Field(default_factory=dict)
    request_hash: str = Field(
        default="",
        description="Stable hash of request payload for matching on replay.",
    )

    def model_post_init(self, __context: Any) -> None:
        if not self.request_hash and self.request:
            self.request_hash = hash_interaction_request(self.kind, self.name, self.request)


class AgentRun(BaseModel):
    """Metadata + interactions for a single recorded run."""

    name: str
    recorded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent_id: str = "default"
    interactions: list[Interaction] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def tool_sequence(self) -> list[str]:
        return [i.name for i in self.interactions if i.kind == InteractionKind.TOOL]


class Cassette(BaseModel):
    """File container; may hold multiple named runs (e.g. parametrize)."""

    schema_version: int = 1
    runs: dict[str, AgentRun] = Field(default_factory=dict)

    def get_run(self, name: str) -> AgentRun | None:
        return self.runs.get(name)

    def add_run(self, run: AgentRun) -> None:
        self.runs[run.name] = run


def hash_interaction_request(kind: InteractionKind, name: str, request: dict[str, Any]) -> str:
    payload = json.dumps(
        {"kind": kind.value, "name": name, "request": request},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def load_cassette(path: Path) -> Cassette:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return Cassette.model_validate(raw)


def save_cassette(path: Path, cassette: Cassette) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = cassette.model_dump(mode="json")
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def cassette_path(base_dir: Path, test_name: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in test_name)
    return base_dir / f"{safe}.yaml"
