from pathlib import Path

from tapeagent.cli import build_parser, cmd_verify


def test_verify_cli_success() -> None:
    manifest = Path(__file__).resolve().parents[1] / "examples" / "verify_manifest.yaml"
    parser = build_parser()
    args = parser.parse_args(["verify", str(manifest)])
    assert cmd_verify(args) == 0
