# Contributing

## Setup

```bash
make install
make test
```

## When agent behavior changes intentionally

1. Update code in `src/tapeagent/demo/simple_agent.py` or your agent.
2. Re-record cassettes:

   ```bash
   make record
   ```

3. Commit updated YAML under `src/tapeagent/demo/cassettes/`.
4. Run `make verify` and `make test` before opening a PR.

## Cassette hygiene

- Do not commit API keys; cassettes store LLM **responses**, not secrets.
- Keep requests stable (hashes detect argument drift on replay).
- Prefer small, focused scenarios over one giant cassette.

## Release checklist

- [ ] `pytest -q` passes with `TAPEAGENT_MODE=replay`
- [ ] `tapeagent verify examples/verify_manifest.yaml`
- [ ] README metrics / version bumped in `pyproject.toml`
