# TapeAgent architecture

## Cassette model

Each YAML file holds one or more **named runs**. A run is an ordered list of **interactions**:

1. **LLM** — request payload (messages, params) + response (content, tool_calls).
2. **TOOL** — tool name, arguments, and serializable result.

Request hashes let replay fail fast when the agent sends a different tool argument shape than recorded.

## Session lifecycle

```
AUTO mode → cassette missing? RECORD : REPLAY
RECORD    → append interactions → flush on exit
REPLAY    → walk interactions in order; stub LLM/tool outputs
```

`TapedLLM` and `TapedOpenAI` keep application call sites unchanged: on replay, live LLM clients are not invoked.

## Verification pipeline

`examples/verify_manifest.yaml` lists scenarios:

- `name` — cassette run key
- `cassette_dir` — directory of YAML files
- `entrypoint` — `module:callable(session)` executed under `TapeMode.REPLAY`

`tapeagent verify` loads the manifest, runs each scenario, and exits non-zero on failure. The composite Action wraps the same command for other repos.

## Pytest plugin

- Marker: `@pytest.mark.tape("run_name", cassette_dir=..., mode=...)`
- Fixture: `tape_session` (requires the marker on the same test)
- CLI flags: `--tape-mode`, `--tape-cassette-dir`

## Regression signals

| Signal | Meaning |
|--------|---------|
| Tool sequence change | Model/prompt likely changed agent plan |
| Request hash mismatch | Same tool, different args |
| LLM text diff | Optional compare via `compare_runs(compare_llm_text=True)` |

## CI layout

1. `pytest` with `TAPEAGENT_MODE=replay` (unit + plugin + integration)
2. `tapeagent verify examples/verify_manifest.yaml`
3. Optional: `python -m build` on release branches
