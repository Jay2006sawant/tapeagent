.PHONY: install test record verify demo lint clean

install:
	python3 -m venv .venv
	.venv/bin/pip install -U pip
	.venv/bin/pip install -e ".[dev]"

test:
	TAPEAGENT_MODE=replay .venv/bin/pytest -q

record:
	TAPEAGENT_MODE=record .venv/bin/python -c "\
from tapeagent.demo.simple_agent import run_weather_scenario, run_policy_scenario; \
run_weather_scenario(); run_policy_scenario(); \
print('Cassettes updated in src/tapeagent/demo/cassettes/')"

verify:
	TAPEAGENT_MODE=replay .venv/bin/tapeagent verify examples/verify_manifest.yaml

demo:
	TAPEAGENT_MODE=replay .venv/bin/python examples/simple_agent/agent.py

lint:
	.venv/bin/python -m compileall -q src tests

clean:
	rm -rf .pytest_cache dist build *.egg-info .venv
