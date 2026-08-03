from __future__ import annotations

import json
from pathlib import Path

from product_decision_os.cli import main

from .test_validator import install_adapter, install_schemas, metadata, write_artifact


def test_cli_validate_json_contract(tmp_path: Path, capsys) -> None:
    install_schemas(tmp_path)
    write_artifact(tmp_path, metadata())
    exit_code = main(["validate", str(tmp_path), "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["command"] == "validate"
    assert payload["ok"] is True
    assert payload["exit_code"] == 0
    assert captured.err == ""


def test_cli_validation_failure_is_exit_one_and_stderr(tmp_path: Path, capsys) -> None:
    install_schemas(tmp_path)
    data = metadata()
    data["relationships"] = {"signals": ["signal_MJSSJNGX"]}
    write_artifact(tmp_path, data)
    exit_code = main(["validate", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "BROKEN_INTERNAL_REFERENCE" in captured.err


def test_cli_invocation_failure_is_exit_two_and_json(tmp_path: Path, capsys) -> None:
    exit_code = main(["unknown", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert payload["exit_code"] == 2
    assert payload["errors"][0]["code"] == "INVOCATION_ERROR"


def test_cli_default_workspace_and_json_before_command(tmp_path: Path, capsys, monkeypatch) -> None:
    install_schemas(tmp_path)
    write_artifact(tmp_path, metadata())
    monkeypatch.chdir(tmp_path)
    assert main(["--json", "validate"]) == 0
    assert json.loads(capsys.readouterr().out)["workspace"] == str(tmp_path.resolve())


def test_cli_adapter_check_command(tmp_path: Path, capsys) -> None:
    install_adapter(tmp_path)
    assert main(["adapter-check", str(tmp_path)]) == 0
    assert "PASS adapter-check" in capsys.readouterr().out


def test_cli_accepts_base_ref_override(tmp_path: Path, capsys) -> None:
    install_schemas(tmp_path)
    data = metadata("opportunity", "opportunity_01DECJDE")
    data["decision_events"] = [
        {
            "id": "decision_01BASEXX",
            "kind": "opportunity",
            "choice": "pursue",
        }
    ]
    write_artifact(tmp_path, data)
    assert main(["validate", str(tmp_path), "--base-ref", "origin/main", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["warnings"][0]["code"] == "DECISION_BASELINE_UNAVAILABLE"
