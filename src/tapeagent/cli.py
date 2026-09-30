"""CLI: compare cassettes, show tool sequences."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from tapeagent.cassette import load_cassette
from tapeagent.diff import compare_runs
from tapeagent.verify import verify_manifest

console = Console()


def cmd_show(args: argparse.Namespace) -> int:
    cassette = load_cassette(Path(args.cassette))
    run = cassette.get_run(args.run)
    if run is None:
        console.print(f"[red]Run {args.run!r} not found[/red]")
        return 1

    table = Table(title=f"Run: {args.run}")
    table.add_column("#", style="dim")
    table.add_column("Kind")
    table.add_column("Name")
    table.add_column("Summary")

    for i, inter in enumerate(run.interactions):
        summary = ""
        if inter.kind.value == "llm":
            content = inter.response.get("content", "")
            summary = (content[:80] + "…") if len(str(content)) > 80 else str(content)
        else:
            summary = str(inter.response.get("result", ""))[:80]
        table.add_row(str(i), inter.kind.value, inter.name, summary)

    console.print(table)
    console.print(f"Tool sequence: {run.tool_sequence}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    left = load_cassette(Path(args.baseline)).get_run(args.run)
    right = load_cassette(Path(args.candidate)).get_run(args.run)
    if left is None or right is None:
        console.print("[red]Missing run in one of the cassettes[/red]")
        return 1

    result = compare_runs(left, right)
    if result.ok:
        console.print("[green]Runs match[/green]")
        return 0

    console.print("[red]Runs differ[/red]")
    console.print(result.summary())
    if args.json:
        print(
            json.dumps(
                {
                    "ok": result.ok,
                    "tool_sequence_changed": result.tool_sequence_changed,
                    "baseline_tools": result.baseline_tools,
                    "candidate_tools": result.candidate_tools,
                    "mismatches": result.interaction_mismatches,
                },
                indent=2,
            )
        )
    return 2


def cmd_verify(args: argparse.Namespace) -> int:
    results = verify_manifest(Path(args.manifest))
    failures = 0
    for name, outcome in results:
        if isinstance(outcome, Exception):
            console.print(f"[red]FAIL[/red] {name}: {outcome}")
            failures += 1
        else:
            preview = outcome if len(outcome) < 100 else outcome[:97] + "..."
            console.print(f"[green]OK[/green] {name}: {preview}")
    return 1 if failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tapeagent", description="Agent run cassettes")
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="Print interactions for a run")
    show.add_argument("cassette", type=str)
    show.add_argument("run", type=str)
    show.set_defaults(func=cmd_show)

    diff = sub.add_parser("diff", help="Compare the same run name in two cassettes")
    diff.add_argument("baseline", type=str)
    diff.add_argument("candidate", type=str)
    diff.add_argument("run", type=str)
    diff.add_argument("--json", action="store_true")
    diff.set_defaults(func=cmd_diff)

    verify = sub.add_parser("verify", help="Replay all scenarios in a manifest (CI)")
    verify.add_argument("manifest", type=str, help="Path to verify_manifest.yaml")
    verify.set_defaults(func=cmd_verify)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    code = args.func(args)
    sys.exit(code)


if __name__ == "__main__":
    main()
