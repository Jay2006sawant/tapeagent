# How to deploy and show TapeAgent to companies

TapeAgent is a **developer tool / library**, not a consumer web app. You do **not** need Heroku or a chat URL for it to look credible. Companies judge **public repo + green CI + clear README + short demo**.

## What “deployed” means for this project

| Artifact | What recruiters see | Required? |
|----------|---------------------|-----------|
| **Public GitHub repo** | Source, commits, professionalism | **Yes** |
| **Green GitHub Actions** | Tests + `tapeagent verify` on every push | **Yes** |
| **README** | Problem, architecture, quick start | **Yes** |
| **2–3 min demo video** (Loom / YouTube unlisted) | You explain + terminal replay | **Strongly yes** |
| **PyPI** (`pip install tapeagent`) | Optional extra signal | Nice |
| **Live website** | Only if you add a docs/trace UI later | No for v1 |

**Interview live demo (no deploy):** screen-share terminal:

```bash
git clone https://github.com/Jay2006sawant/tapeagent.git && cd tapeagent
make install && make verify
tapeagent show src/tapeagent/demo/cassettes/weather_query.yaml weather_query
```

CI runs the same thing without your laptop — link the Actions tab in the README.

---

## Checklist before sharing on resume (≈1 evening)

1. [ ] Create **public** repo `tapeagent` on GitHub (no secrets in history).
2. [ ] Initial commit; push `master` or `main`.
3. [ ] Confirm **Actions** pass (Actions tab all green).
4. [ ] Replace placeholder links in README if you fork the repository.
5. [ ] Record **Loom**: 90s problem → 60s `make verify` → 30s cassette YAML snippet.
6. [ ] Add repo + video link to resume, LinkedIn, placement form.
7. [ ] (Optional) Publish to PyPI — see below.

---

## Push to GitHub (first time)

```bash
cd /home/jay/Projects/tapeagent
git add -A
git commit -m "Initial release: TapeAgent record/replay testing for LLM agents"
# Create empty repo on github.com/new → name: tapeagent → Public
git remote add origin https://github.com/Jay2006sawant/tapeagent.git
git branch -M main
git push -u origin main
```

Then open **Settings → Actions → General** and allow workflows if prompted.

Badges to paste at top of README after push (replace user):

```markdown
[![CI](https://github.com/Jay2006sawant/tapeagent/actions/workflows/ci.yml/badge.svg)](https://github.com/Jay2006sawant/tapeagent/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
```

---

## What to put on your resume (copy, edit numbers)

**Project line:** TapeAgent — open-source regression testing for LLM tool agents (Python).

**Bullet 1:** Built record/replay **cassettes** (VCR pattern) for LLM + tool-call traces; CI runs in **replay mode with $0 API cost**.

**Bullet 2:** Shipped **pytest plugin**, **CLI** (`verify`, `diff`), **OpenAI shim**, and composite **GitHub Action**; **9 automated tests** on Python 3.10–3.12.

**Bullet 3:** Demo agent + committed cassettes; `tapeagent verify` fails CI when tool order or request hashes regress.

**Skills tags:** Python, pytest, CI/CD, GitHub Actions, LLM agents, testing, YAML, developer tools.

---

## 30-second interview pitch (memorize)

> “Agents break when you change prompts or models, but teams rarely test that. I built **TapeAgent** — like **VCR for agents**. Locally you **record** LLM turns and tool calls to a cassette; in **CI you replay** with no API keys. If the agent picks a different tool or different arguments, tests fail. It’s on GitHub with a pytest plugin, a verify CLI, and Actions running on every PR.”

---

## 2-minute live demo script

1. **Problem (15s):** “Non-deterministic agents; need regression tests, not eyeballing chat.”
2. **Show cassette (20s):** Open `weather_query.yaml` — LLM step + `get_weather` tool.
3. **Replay (30s):** `make verify` — both scenarios OK.
4. **Break intentionally (45s):** Change `fake_llm` to call a different tool → `make test` fails on replay / hash mismatch.
5. **Close (10s):** “Framework is generic; demo agent is mocked so CI is free. Real usage: record once with OpenAI via `TapedOpenAI`, replay forever in CI.”

---

## FAQ recruiters ask

**“Is this just a chatbot?”**  
No — it’s **testing infrastructure** for agents. The chat-like demo only exercises the library.

**“Did you use a real LLM?”**  
Cassettes are from a **deterministic mock** for CI. The **OpenAI shim** is implemented and tested; production flow is record with API once, replay in CI. (If you record one real cassette later, say so honestly.)

**“Why not just mock in tests?”**  
Mocks hide integration drift. Cassettes capture **full multi-step** LLM + tool traces and detect **sequence** changes.

**“Who would use this?”**  
Any team shipping tool-using agents — same niche as LLM observability / eval tooling.

---

## Optional: PyPI (extra credibility)

```bash
pip install build twine
python -m build
# Create account on pypi.org
twine upload dist/*
```

Then add to README: `pip install tapeagent`

---

## Optional: stronger story in 2 weeks

| Add-on | Why |
|--------|-----|
| One **real** recorded cassette (your API key, local only, redacted request) | Proves record path |
| **Blog post** on Medium/dev.to (architecture + tradeoffs) | Shareable link |
| **Issue / RFC** “LLM-judge diff mode” | Shows product thinking |
| Star your own repo only after public launch; ask 5 classmates to try `pip install -e .` | Soft validation |

---

## What NOT to claim

- Don’t say “production deployment on AWS” unless you actually run a service.
- Don’t inflate download numbers before PyPI is live.
- Don’t call it a RAG product — it’s **agent testing**.

Your strongest links in applications: **GitHub URL**, **green CI screenshot or badge**, **demo video URL**.
