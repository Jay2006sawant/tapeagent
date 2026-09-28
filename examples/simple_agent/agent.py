#!/usr/bin/env python3
"""CLI entry for the reference agent (see tapeagent.demo.simple_agent)."""

from tapeagent.demo.simple_agent import run_policy_scenario, run_weather_scenario

if __name__ == "__main__":
    print(run_weather_scenario())
    print("---")
    print(run_policy_scenario())
