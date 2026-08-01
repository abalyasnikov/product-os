from __future__ import annotations

from pathlib import Path

import pytest
import yaml


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_skill(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} has no YAML frontmatter"
    _, frontmatter, body = text.split("---", 2)
    return yaml.safe_load(frontmatter), body
