"""Compare recorded vs replayed agent runs."""

from __future__ import annotations

from dataclasses import dataclass, field

from tapeagent.cassette import AgentRun, Interaction, InteractionKind


@dataclass
class RunDiff:
    """Structured differences between a baseline and a candidate run."""

    ok: bool
    tool_sequence_changed: bool
    baseline_tools: list[str]
    candidate_tools: list[str]
    interaction_mismatches: list[str] = field(default_factory=list)
    message: str = ""

    def summary(self) -> str:
        if self.ok:
            return "Runs match (tool sequence and recorded responses)."
        parts = [self.message or "Regression detected."]
        if self.tool_sequence_changed:
            parts.append(
                f"Tool sequence: {self.baseline_tools!r} -> {self.candidate_tools!r}"
            )
        parts.extend(self.interaction_mismatches[:10])
        return " ".join(parts)


def compare_runs(
    baseline: AgentRun,
    candidate: AgentRun,
    *,
    compare_llm_text: bool = True,
    compare_tool_results: bool = True,
) -> RunDiff:
    base_tools = baseline.tool_sequence
    cand_tools = candidate.tool_sequence
    tool_changed = base_tools != cand_tools

    mismatches: list[str] = []

    if len(baseline.interactions) != len(candidate.interactions):
        mismatches.append(
            f"Interaction count {len(baseline.interactions)} vs {len(candidate.interactions)}"
        )

    for idx, (b, c) in enumerate(zip(baseline.interactions, candidate.interactions)):
        mismatches.extend(_diff_interaction(idx, b, c, compare_llm_text, compare_tool_results))

    ok = not tool_changed and not mismatches
    return RunDiff(
        ok=ok,
        tool_sequence_changed=tool_changed,
        baseline_tools=base_tools,
        candidate_tools=cand_tools,
        interaction_mismatches=mismatches,
        message="" if ok else "Agent behavior diverged from cassette.",
    )


def _diff_interaction(
    idx: int,
    baseline: Interaction,
    candidate: Interaction,
    compare_llm_text: bool,
    compare_tool_results: bool,
) -> list[str]:
    out: list[str] = []
    if baseline.kind != candidate.kind or baseline.name != candidate.name:
        out.append(
            f"[{idx}] kind/name {baseline.kind.value}/{baseline.name} "
            f"!= {candidate.kind.value}/{candidate.name}"
        )
        return out

    if baseline.kind == InteractionKind.LLM and compare_llm_text:
        b_text = _llm_text(baseline.response)
        c_text = _llm_text(candidate.response)
        if b_text != c_text:
            out.append(f"[{idx}] LLM response text differs")

    if baseline.kind == InteractionKind.TOOL and compare_tool_results:
        b_res = baseline.response.get("result")
        c_res = candidate.response.get("result")
        if b_res != c_res:
            out.append(f"[{idx}] tool {baseline.name!r} result differs")

    return out


def _llm_text(response: dict) -> str:
    if "content" in response:
        return str(response["content"])
    if "message" in response and isinstance(response["message"], dict):
        return str(response["message"].get("content", ""))
    return json_dumps_stable(response)


def json_dumps_stable(obj: object) -> str:
    import json

    return json.dumps(obj, sort_keys=True, default=str)
