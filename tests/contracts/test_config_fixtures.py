from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
CONFIG_FIXTURES = ROOT / "tests" / "fixtures" / "config"


def _errors(path: Path) -> list:
    schema = json.loads((ROOT / "schemas" / "config.schema.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    return list(Draft202012Validator(schema).iter_errors(config))


def test_valid_config_fixtures_match_canonical_schema() -> None:
    for name in ("valid-solo.yaml", "valid-provider.yaml"):
        assert _errors(CONFIG_FIXTURES / name) == [], name


def test_invalid_config_fixtures_fail_canonical_schema() -> None:
    fixtures = sorted((CONFIG_FIXTURES / "invalid").glob("*.yaml"))
    assert fixtures
    for path in fixtures:
        assert _errors(path), path.name
