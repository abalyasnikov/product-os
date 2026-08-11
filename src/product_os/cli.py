"""Command-line interface for deterministic Product OS validation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

import yaml

from datetime import date

from .queue import compute_queue, render as render_queue
from .validator import ValidationReport, validate_workspace


# `check` verifies the repository; `queue` reads it. Neither writes. The three older check names
# stay accepted so existing scripts keep working, but they are not advertised: splitting the
# checks is what let a fabricated approval version pass the command the authoring loop called.
COMMANDS = ("check", "queue", "validate", "smoke-test", "adapter-check")
DEPRECATED_COMMANDS = {"validate", "smoke-test", "adapter-check"}


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="product-os",
        description="Check a Product OS workspace: schemas, graph, append-only decisions, "
        "approval versions, evidence policy, and generated adapters.",
    )
    parser.add_argument("command", choices=COMMANDS, metavar="{check,queue}")
    parser.add_argument("workspace", nargs="?", default=".")
    parser.add_argument(
        "--base-ref",
        help="Git commit or branch used to verify append-only decision events (default: workspace config or HEAD)",
    )
    parser.add_argument(
        "--as-of",
        help="queue only: the date review dates are judged against (default: today, UTC)",
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
        if args.command == "queue":
            # Computed on request and printed. Nothing here writes to the workspace.
            queue = compute_queue(
                Path(args.workspace),
                as_of=date.fromisoformat(args.as_of) if args.as_of else None,
            )
            print(json.dumps(queue.to_dict(), indent=2, sort_keys=True) if json_output else render_queue(queue))
            return 0
        report = validate_workspace(Path(args.workspace), command=args.command, base_ref=args.base_ref)
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError, yaml.YAMLError, subprocess.SubprocessError) as exc:
        workspace = Path(".").resolve()
        report = ValidationReport(command="invocation", workspace=workspace, configuration_error=True)
        report.error(
            "INVOCATION_ERROR",
            " ".join(str(exc).split())[:400],
            hint="Use: product-os {check,queue} [workspace] [--json] [--base-ref REF] [--as-of DATE]",
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
