"""Safe Markdown frontmatter parsing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from yaml.events import AliasEvent


class FrontmatterError(ValueError):
    """Raised when a Markdown document has invalid YAML frontmatter."""


class _StrictSafeLoader(yaml.SafeLoader):
    max_nodes = 10_000
    max_depth = 100

    def __init__(self, stream: str) -> None:
        super().__init__(stream)
        self._node_count = 0
        self._node_depth = 0

    def compose_node(self, parent: yaml.Node | None, index: int | None) -> yaml.Node:
        if self.check_event(AliasEvent):
            raise FrontmatterError("YAML aliases are not allowed")
        self._node_count += 1
        if self._node_count > self.max_nodes:
            raise FrontmatterError(f"YAML exceeds the {self.max_nodes}-node safety budget")
        self._node_depth += 1
        if self._node_depth > self.max_depth:
            raise FrontmatterError(f"YAML exceeds the {self.max_depth}-level depth safety budget")
        try:
            return super().compose_node(parent, index)
        finally:
            self._node_depth -= 1


def _construct_mapping(loader: yaml.Loader, node: yaml.Node, deep: bool = False) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise FrontmatterError(f"duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


@dataclass(frozen=True)
class MarkdownDocument:
    path: Path
    metadata: dict[str, Any]
    body: str
    raw: str


def parse_markdown(path: Path, *, max_bytes: int = 2_000_000) -> MarkdownDocument:
    """Parse UTF-8 Markdown with a required, safe YAML frontmatter mapping."""
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise FrontmatterError(f"cannot read file metadata: {exc}") from exc
    if size > max_bytes:
        raise FrontmatterError(
            f"file is {size} bytes; artifact files may not exceed {max_bytes} bytes"
        )
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise FrontmatterError(f"cannot read UTF-8 file: {exc}") from exc

    return parse_markdown_text(raw, path=path)


def parse_markdown_text(raw: str, *, path: Path = Path("<memory>")) -> MarkdownDocument:
    """Parse Markdown already loaded in memory, including content read from Git."""
    lines = raw.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("Markdown artifact must start with a '---' YAML delimiter")
    closing = next((index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if closing is None:
        raise FrontmatterError("YAML frontmatter is missing its closing '---' delimiter")
    yaml_text = "".join(lines[1:closing])
    try:
        loaded = load_yaml_strict(yaml_text)
    except FrontmatterError:
        raise
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        location = f" at line {mark.line + 2}, column {mark.column + 1}" if mark else ""
        raise FrontmatterError(f"invalid YAML{location}: {exc}") from exc
    if loaded is None:
        loaded = {}
    if not isinstance(loaded, dict):
        raise FrontmatterError("YAML frontmatter must be an object, not a list or scalar")
    return MarkdownDocument(path=path, metadata=loaded, body="".join(lines[closing + 1 :]), raw=raw)


def load_yaml_strict(raw: str) -> Any:
    """Load YAML without aliases and with bounded composition."""
    return yaml.load(raw, Loader=_StrictSafeLoader)
