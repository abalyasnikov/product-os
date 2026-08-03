"""Command-line interface for deterministic Product OS validation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

import yaml

from .validator import ValidationReport, validate_workspace


COMMANDS = ("validate", "smoke-test", "adapter-check")


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="product-os", description="Validate a Product OS workspace")
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("workspace", nargs="?", default=".")
    parser.add_argument(
        "--base-ref",
        help="Git commit or branch used to verify append-only decision events (default: workspace config or HEAD)",
    )
    return parser


def _render_text(report: ValidationReport) -> str:
    state = "PASS" if report.ok else "FAIL"
    lines = [f"{state} {report.command} {report.workspace}"]
    for issue in report.errors:
        location = f" {issue.path}" if issue.path else ""
        field = f" ({issue.field})" if issue.field else ""
        lines.append(f"ERROR [{issue.code}]{location}{field}: {issue.message}")
        if issue.hint:
            lines.append(f"  Fix: {issue.hint}")
    for issue in report.warnings:
        location = f" {issue.path}" if issue.path else ""
        lines.append(f"WARN [{issue.code}]{location}: {issue.message}")
    lines.append(
        f"{report.artifact_count} artifact(s), {len(report.errors)} error(s), "
        f"{len(report.warnings)} warning(s)"
    )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    json_output = "--json" in args_list
    args_list = [arg for arg in args_list if arg != "--json"]
    try:
        args = _parser().parse_args(args_list)
        report = validate_workspace(Path(args.workspace), command=args.command, base_ref=args.base_ref)
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError, yaml.YAMLError, subprocess.SubprocessError) as exc:
        workspace = Path(".").resolve()
        report = ValidationReport(command="invocation", workspace=workspace, configuration_error=True)
        report.error(
            "INVOCATION_ERROR",
            " ".join(str(exc).split())[:400],
            hint="Use: product-os {validate,smoke-test,adapter-check} [workspace] [--json] [--base-ref REF]",
        )
    except Exception as exc:  # keep the CLI machine-readable at trust boundaries
        workspace = Path(".").resolve()
        report = ValidationReport(command="invocation", workspace=workspace, configuration_error=True)
        report.error(
            "CONFIGURATION_ERROR",
            f"Validation could not start safely: {' '.join(str(exc).split())[:300]}",
            hint="Check workspace readability and installed schemas, then retry.",
        )
    if json_output:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(_render_text(report), file=sys.stdout if report.ok else sys.stderr)
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
