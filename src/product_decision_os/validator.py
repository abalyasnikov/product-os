"""Product OS workspace validators."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError
from referencing import Registry, Resource

from .frontmatter import (
    FrontmatterError,
    MarkdownDocument,
    load_yaml_strict,
    markdown_sections,
    parse_markdown,
    parse_markdown_text,
    structured_blocks,
)


TYPE_CONFIG: dict[str, tuple[str, str]] = {
    "signal": ("signal_", "signals"),
    "pattern": ("pattern_", "patterns"),
    "opportunity": ("opportunity_", "opportunities"),
    "initiative": ("initiative_", "initiatives"),
    "prd": ("prd_", "prds"),
    "outcome_contract": ("outcome_", "outcome-contracts"),
    "learning": ("learning_", "learnings"),
    "product_update": ("update_", "updates"),
}
PREFIX_TO_TYPE = {prefix: artifact_type for artifact_type, (prefix, _) in TYPE_CONFIG.items()}
RELATIONSHIP_TARGETS: dict[str, str] = {
    "signal": "signal_",
    "signals": "signal_",
    "pattern": "pattern_",
    "patterns": "pattern_",
    "opportunity": "opportunity_",
    "opportunities": "opportunity_",
    "initiative": "initiative_",
    "initiatives": "initiative_",
    "prd": "prd_",
    "prds": "prd_",
    "outcome_contract": "outcome_",
    "outcome_contracts": "outcome_",
    "learning": "learning_",
    "learnings": "learning_",
    "update": "update_",
    "updates": "update_",
}
INTERNAL_ID_RE = re.compile(
    r"^(?:signal|pattern|opportunity|initiative|prd|outcome|learning|update)_[0-9A-HJKMNP-TV-Z]{8,32}$"
)
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
SPEAKER_LINE_RE = re.compile(
    r"(?im)^(?:\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s*)?(?:speaker\s*\d+|interviewer|participant|host|guest|[A-Z][\w .'-]{1,35}):\s+"
)

CREDENTIAL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[opusr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("authorization bearer token", re.compile(r"(?i)\bauthorization\s*:\s*bearer\s+[A-Za-z0-9._~+/=-]{12,}")),
    (
        "credential assignment",
        re.compile(
            r"(?im)^\s*(?:api[_-]?key|access[_-]?token|client[_-]?secret|password|secret[_-]?key)\s*[:=]\s*[\"']?(?!example\b|redacted\b|placeholder\b|none\b|null\b|\$\{)[A-Za-z0-9_./+~=-]{12,}"
        ),
    ),
)
PII_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"(?<!\w)\+[1-9](?:[ .()-]*\d){7,14}(?!\w)"),
)


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    path: str | None = None
    artifact_id: str | None = None
    field: str | None = None
    hint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass
class CheckResult:
    name: str
    status: str
    details: str


@dataclass
class ValidationReport:
    command: str
    workspace: Path
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    artifact_count: int = 0
    configuration_error: bool = False

    @property
    def ok(self) -> bool:
        return not self.errors and not self.configuration_error

    @property
    def exit_code(self) -> int:
        if self.configuration_error:
            return 2
        return 0 if self.ok else 1

    def error(self, code: str, message: str, **context: Any) -> None:
        self.errors.append(Issue(code=code, message=message, **context))

    def warning(self, code: str, message: str, **context: Any) -> None:
        self.warnings.append(Issue(code=code, message=message, **context))

    def check(self, name: str, before_errors: int, details: str) -> None:
        status = "pass" if len(self.errors) == before_errors else "fail"
        self.checks.append(CheckResult(name=name, status=status, details=details))

    def sort_issues(self) -> None:
        key = lambda issue: (issue.path or "", issue.artifact_id or "", issue.field or "", issue.code, issue.message)
        self.errors.sort(key=key)
        self.warnings.sort(key=key)

    def to_dict(self) -> dict[str, Any]:
        self.sort_issues()
        return {
            "report_version": 1,
            "command": self.command,
            "workspace": str(self.workspace),
            "ok": self.ok,
            "exit_code": self.exit_code,
            "summary": {
                "artifacts": self.artifact_count,
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "checks": len(self.checks),
            },
            "errors": [issue.to_dict() for issue in self.errors],
            "warnings": [issue.to_dict() for issue in self.warnings],
            "checks": [asdict(check) for check in self.checks],
        }


def _relative(path: Path, workspace: Path) -> str:
    try:
        return path.relative_to(workspace).as_posix()
    except ValueError:
        return str(path)


def _normalize_type(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {"outcome": "outcome_contract", "update": "product_update"}
    return aliases.get(normalized, normalized)


def _json_value(value: Any, _seen: set[int] | None = None) -> Any:
    seen = _seen if _seen is not None else set()
    if isinstance(value, (date, datetime)):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in seen:
            return "<cyclic-structure-rejected>"
        seen.add(identity)
        try:
            return {str(key): _json_value(child, seen) for key, child in value.items()}
        finally:
            seen.remove(identity)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        identity = id(value)
        if identity in seen:
            return "<cyclic-structure-rejected>"
        seen.add(identity)
        try:
            return [_json_value(child, seen) for child in value]
        finally:
            seen.remove(identity)
    return value


def _walk(
    value: Any,
    path: tuple[str, ...] = (),
    _seen: set[int] | None = None,
) -> Iterator[tuple[tuple[str, ...], Any]]:
    seen = _seen if _seen is not None else set()
    yield path, value
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in seen:
            return
        seen.add(identity)
        try:
            for key, child in value.items():
                yield from _walk(child, path + (str(key),), seen)
        finally:
            seen.remove(identity)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        identity = id(value)
        if identity in seen:
            return
        seen.add(identity)
        try:
            for index, child in enumerate(value):
                yield from _walk(child, path + (str(index),), seen)
        finally:
            seen.remove(identity)


def _has(mapping: Mapping[str, Any], *names: str) -> bool:
    return any(name in mapping and mapping[name] is not None and mapping[name] != "" for name in names)


def _bounded_message(message: str, limit: int = 400) -> str:
    """Keep reports useful without echoing large or sensitive invalid values."""
    compact = " ".join(message.split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


_TOP_LEVEL_SCHEMA_WRAPPERS = frozenset({"anyOf", "oneOf", "unevaluatedProperties", "additionalProperties"})


def _actionable_schema_errors(errors: Iterable[ValidationError]) -> list[ValidationError]:
    """Recover useful child failures and hide misleading root composition noise."""
    recovered: list[ValidationError] = []

    def recover(error: ValidationError) -> None:
        if error.validator in {"anyOf", "oneOf"} and not error.absolute_path and error.context:
            for child in error.context:
                recover(child)
            return
        recovered.append(error)

    for error in errors:
        recover(error)

    has_specific_error = any(
        error.validator not in _TOP_LEVEL_SCHEMA_WRAPPERS or bool(error.absolute_path)
        for error in recovered
    )
    if has_specific_error:
        recovered = [
            error
            for error in recovered
            if error.validator not in _TOP_LEVEL_SCHEMA_WRAPPERS or bool(error.absolute_path)
        ]

    unique: dict[tuple[tuple[Any, ...], str, str], ValidationError] = {}
    for error in recovered:
        key = (tuple(error.absolute_path), str(error.validator), error.message)
        unique.setdefault(key, error)
    return sorted(unique.values(), key=lambda error: (tuple(str(part) for part in error.absolute_path), error.message))


def _schema_error_field(error: ValidationError) -> str | None:
    parts = [str(part) for part in error.absolute_path]
    if error.validator == "required":
        match = re.fullmatch(r"'([^']+)' is a required property", error.message)
        if match:
            parts.append(match.group(1))
    return ".".join(parts) or None


def _safe_schema_message(error: ValidationError) -> str:
    """Describe the violated rule without reflecting the invalid instance value."""
    if error.validator == "required":
        match = re.fullmatch(r"'([^']+)' is a required property", error.message)
        return f"Required field '{match.group(1)}' is missing." if match else "A required field is missing."
    if error.validator == "type":
        expected = error.validator_value
        names = ", ".join(str(item) for item in expected) if isinstance(expected, list) else str(expected)
        return f"Value must have the required type: {names}."
    messages = {
        "enum": "Value must be one of the schema's allowed choices.",
        "const": "Value must match the schema's required constant.",
        "pattern": "Value does not match the schema's required format.",
        "format": "Value does not match the schema's required format.",
        "minLength": "Text is shorter than the schema minimum.",
        "maxLength": "Text exceeds the schema maximum.",
        "minimum": "Number is below the schema minimum.",
        "maximum": "Number exceeds the schema maximum.",
        "minItems": "List has fewer items than the schema requires.",
        "maxItems": "List has more items than the schema allows.",
        "uniqueItems": "List contains duplicate items.",
        "additionalProperties": "Object contains fields not allowed by the schema.",
        "unevaluatedProperties": "Object contains fields not allowed by the composed schema.",
        "anyOf": "Value does not satisfy any allowed schema variant.",
        "oneOf": "Value must satisfy exactly one allowed schema variant.",
    }
    return messages.get(str(error.validator), "Value does not satisfy the canonical schema rule.")


class WorkspaceValidator:
    def __init__(self, workspace: Path, command: str = "validate", base_ref: str | None = None) -> None:
        self.workspace = workspace.resolve()
        self.command = command
        self.base_ref = base_ref
        self.report = ValidationReport(command=command, workspace=self.workspace)
        self.documents: list[MarkdownDocument] = []
        self.by_id: dict[str, MarkdownDocument] = {}
        self.config: dict[str, Any] = {}
        self.config_path: Path | None = None
        self._schemas_cache: dict[str, dict[str, Any]] | None = None
        self._schema_validators: dict[str, Draft202012Validator] = {}
        self._distribution_root_cache: Path | None | bool = False
        self.resolved_base_sha: str | None = None
        self._base_ref_source = "unknown"
        self._baseline_failure_reported = False
        self._unsafe_paths_reported: set[str] = set()
        self._fixture_synthetic_cache: bool | None = None
        self.empty_workspace = False

    def run(self) -> ValidationReport:
        if not self.workspace.exists():
            self.report.configuration_error = True
            self.report.error(
                "WORKSPACE_NOT_FOUND",
                "Workspace does not exist.",
                path=str(self.workspace),
                hint="Pass an existing Product OS workspace directory.",
            )
            return self.report
        if not self.workspace.is_dir():
            self.report.configuration_error = True
            self.report.error(
                "WORKSPACE_NOT_DIRECTORY",
                "Workspace path is not a directory.",
                path=str(self.workspace),
                hint="Pass a directory, not an artifact file.",
            )
            return self.report

        if self.command in {"validate", "smoke-test"}:
            self._validate_configuration(required=self.command == "smoke-test")
            self._validate_artifacts()
        if self.command in {"adapter-check", "smoke-test"}:
            self._validate_adapters()
        if self.command == "smoke-test":
            self._smoke_checks()
        self.report.sort_issues()
        return self.report

    def _distribution_root(self) -> Path | None:
        if self._distribution_root_cache is not False:
            return self._distribution_root_cache
        for candidate in (self.workspace, *self.workspace.parents):
            pyproject = candidate / "pyproject.toml"
            manifest = candidate / "manifest.json"
            if not pyproject.is_file() or not manifest.is_file():
                continue
            if pyproject.is_symlink() or manifest.is_symlink():
                self._report_unsafe_path(pyproject if pyproject.is_symlink() else manifest, "distribution metadata")
                continue
            try:
                text = pyproject.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            if re.search(r'(?m)^name\s*=\s*["\']product-decision-os["\']\s*$', text):
                self._distribution_root_cache = candidate
                return candidate
        self._distribution_root_cache = None
        return None

    def _asset_dir(self, name: str) -> Path | None:
        distribution_root = self._distribution_root()
        candidates = (
            (self.workspace / ".product-os" / name, self.workspace),
            (self.workspace / name, self.workspace),
            (distribution_root / name, distribution_root) if distribution_root else None,
        )
        for item in candidates:
            if item is None:
                continue
            candidate, root = item
            if not candidate.exists() and not candidate.is_symlink():
                continue
            if not self._safe_contained_path(candidate, root):
                self._report_unsafe_path(candidate, f"{name} asset")
                continue
            if candidate.is_dir():
                return candidate
        return None

    def _safe_contained_path(self, path: Path, root: Path) -> bool:
        try:
            lexical = path.relative_to(root)
            resolved_root = root.resolve(strict=True)
            path.resolve(strict=True).relative_to(resolved_root)
        except (OSError, ValueError):
            return False
        current = root
        for part in lexical.parts:
            current = current / part
            if current.is_symlink():
                return False
        return True

    def _report_unsafe_path(self, path: Path, purpose: str) -> None:
        key = str(path)
        if key in self._unsafe_paths_reported:
            return
        self._unsafe_paths_reported.add(key)
        self.report.error(
            "SYMLINK_OR_ESCAPE_REJECTED",
            f"The {purpose} path is symlinked, broken, or resolves outside its trusted root.",
            path=_relative(path, self.workspace),
            hint="Replace it with a regular file/directory contained in the workspace or immutable distribution.",
        )

    def _validate_configuration(self, *, required: bool) -> None:
        candidates = (self.workspace / ".product-os" / "config.yaml", self.workspace / "config.yaml")
        self.config_path = next((path for path in candidates if path.is_file() or path.is_symlink()), None)
        if self.config_path is None:
            if required:
                self.report.configuration_error = True
                self.report.error(
                    "CONFIG_MISSING",
                    "Smoke-test requires .product-os/config.yaml.",
                    path=".product-os/config.yaml",
                    hint="Install and configure the canonical workspace config before smoke-test.",
                )
            return
        if not self._safe_contained_path(self.config_path, self.workspace):
            self.report.configuration_error = True
            self._report_unsafe_path(self.config_path, "workspace config")
            return
        try:
            if self.config_path.stat().st_size > 1_000_000:
                raise ValueError("config file exceeds 1000000 bytes")
            loaded = load_yaml_strict(self.config_path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict):
                raise ValueError("config root must be an object")
            self.config = loaded
        except (OSError, UnicodeError, ValueError, yaml.YAMLError):
            self.report.configuration_error = True
            self.report.error(
                "CONFIG_INVALID",
                "Cannot parse workspace config as a strict UTF-8 YAML object.",
                path=_relative(self.config_path, self.workspace),
                hint="Restore a UTF-8 YAML object matching schemas/config.schema.json.",
            )
            return
        schemas = self._load_schemas()
        schema = schemas.get("config")
        if schema is None:
            self.report.configuration_error = True
            self.report.error(
                "CONFIG_SCHEMA_MISSING",
                "Canonical config schema is not installed.",
                path=_relative(self.config_path, self.workspace),
            )
            return
        validator = self._validator_for("config", schema, schemas)
        if validator is None:
            return
        for error in sorted(validator.iter_errors(_json_value(self.config)), key=lambda item: list(item.absolute_path)):
            self.report.configuration_error = True
            self.report.error(
                "CONFIG_SCHEMA_VALIDATION_FAILED",
                _safe_schema_message(error),
                path=_relative(self.config_path, self.workspace),
                field=".".join(str(part) for part in error.absolute_path) or None,
                hint="Update config to match schemas/config.schema.json.",
            )

    def _artifact_paths(self) -> list[Path]:
        product = self.workspace / "product"
        if not product.exists() and not product.is_symlink():
            self.empty_workspace = True
            self.report.warning(
                "EMPTY_WORKSPACE",
                "Workspace has no product artifacts yet; this is valid immediately after setup.",
                path="product",
                hint="Create the first artifact through a canonical workflow when product work begins.",
            )
            return []
        if not product.is_dir():
            self.report.error(
                "PRODUCT_DIRECTORY_INVALID",
                "Existing product path is not a safe artifact directory.",
                path="product",
                hint="Replace it with a regular contained directory.",
            )
            return []
        if not self._safe_contained_path(product, self.workspace):
            self._report_unsafe_path(product, "product artifact directory")
            return []
        paths: list[Path] = []
        before_errors = len(self.report.errors)
        for path in sorted(product.rglob("*")):
            if path.is_symlink():
                self._report_unsafe_path(path, "product tree entry")
                continue
            if not self._safe_contained_path(path, self.workspace):
                self._report_unsafe_path(path, "product artifact")
                continue
            if path.is_file() and path.suffix.lower() != ".md":
                self.report.error(
                    "PRODUCT_TREE_INVALID",
                    "Product tree contains a non-Markdown artifact file.",
                    path=_relative(path, self.workspace),
                    hint="Keep product artifacts as Markdown with strict YAML frontmatter.",
                )
            elif path.is_file():
                paths.append(path)
        if not paths and len(self.report.errors) == before_errors:
            self.empty_workspace = True
            self.report.warning(
                "EMPTY_WORKSPACE",
                "Workspace product tree contains no artifacts yet; this is valid immediately after setup.",
                path="product",
                hint="Create the first artifact through a canonical workflow when product work begins.",
            )
        return paths

    def _validate_artifacts(self) -> None:
        before = len(self.report.errors)
        paths = self._artifact_paths()
        for path in paths:
            try:
                self.documents.append(parse_markdown(path))
            except FrontmatterError as exc:
                self.report.error(
                    "FRONTMATTER_INVALID",
                    str(exc),
                    path=_relative(path, self.workspace),
                    hint="Use a top-level YAML object between opening and closing '---' delimiters.",
                )
        self.report.artifact_count = len(self.documents)
        self.report.check("frontmatter", before, f"parsed {len(self.documents)} artifact(s)")

        before = len(self.report.errors)
        schemas = self._load_schemas()
        for document in self.documents:
            self._validate_envelope(document)
            self._validate_schema(document, schemas)
        self.report.check("schemas-and-envelope", before, f"validated {len(self.documents)} artifact envelope(s)")

        before = len(self.report.errors)
        self._index_ids()
        self._validate_relationships()
        self._validate_typed_references()
        self._validate_product_graph_contracts()
        self.report.check("ids-and-relationships", before, f"indexed {len(self.by_id)} unique artifact ID(s)")

        before = len(self.report.errors)
        if not self.empty_workspace:
            self._validate_decision_events()
        baseline_detail = (
            f"resolved baseline SHA {self.resolved_base_sha}"
            if self.resolved_base_sha
            else "baseline unavailable"
        )
        self.report.check("decision-event-history", before, f"checked event identity and append-only Git history; {baseline_detail}")

        before = len(self.report.errors)
        for document in self.documents:
            self._validate_evidence(document)
        self.report.check("evidence-policy", before, "checked excerpts, transcript content, and credential patterns")

        before = len(self.report.errors)
        for document in self.documents:
            artifact_type = _normalize_type(document.metadata.get("type"))
            if artifact_type in {"prd", "initiative"}:
                self._validate_readable_document_contract(document)
            if artifact_type in {"prd", "initiative", "outcome_contract"}:
                self._validate_outcome(document)
            if artifact_type == "learning":
                self._validate_learning_anchor(document)
                self._validate_learning_versions(document)
            if artifact_type == "prd":
                self._validate_implementation_refs(document)
        self.report.check("delivery-and-measurement-readiness", before, "checked outcome bindings, anchors, and implementation references")

    def _load_schemas(self) -> dict[str, dict[str, Any]]:
        if self._schemas_cache is not None:
            return self._schemas_cache
        schema_dir = self._asset_dir("schemas")
        if schema_dir is None:
            self.report.error(
                "SCHEMAS_MISSING",
                "No schemas directory is available.",
                hint="Install schemas/ in the workspace or .product-os/schemas before validation.",
            )
            self._schemas_cache = {}
            return self._schemas_cache
        schemas: dict[str, dict[str, Any]] = {}
        for path in sorted(schema_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".json", ".yaml", ".yml"}:
                continue
            if not self._safe_contained_path(path, schema_dir):
                self._report_unsafe_path(path, "schema asset")
                continue
            try:
                raw = path.read_text(encoding="utf-8")
                value = json.loads(raw) if path.suffix.lower() == ".json" else load_yaml_strict(raw)
                if not isinstance(value, dict):
                    raise ValueError("schema root must be an object")
                Draft202012Validator.check_schema(value)
            except (OSError, UnicodeError, ValueError, yaml.YAMLError, SchemaError) as exc:
                self.report.error(
                    "SCHEMA_DEFINITION_INVALID",
                    f"Cannot load schema: {exc}",
                    path=_relative(path, self.workspace),
                    hint="Fix or reinstall the canonical schema file.",
                )
                continue
            stem = path.name.lower()
            for suffix in (".schema.json", ".schema.yaml", ".schema.yml", ".json", ".yaml", ".yml"):
                if stem.endswith(suffix):
                    stem = stem[: -len(suffix)]
                    break
            key = _normalize_type(stem) or stem
            schemas[key] = value
            schemas[path.name] = value
            if "$id" in value:
                schemas[str(value["$id"])] = value
        if not schemas:
            self.report.error(
                "SCHEMAS_EMPTY",
                "Schemas directory contains no readable JSON or YAML schemas.",
                path=_relative(schema_dir, self.workspace),
            )
        self._schemas_cache = schemas
        return self._schemas_cache

    def _validator_for(
        self,
        key: str,
        schema: dict[str, Any],
        schemas: Mapping[str, dict[str, Any]],
    ) -> Draft202012Validator | None:
        cached = self._schema_validators.get(key)
        if cached is not None:
            return cached
        try:
            resources = {
                str(candidate["$id"]): Resource.from_contents(candidate)
                for candidate in schemas.values()
                if isinstance(candidate, dict) and "$id" in candidate
            }
            registry = Registry().with_resources(resources.items())
            validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
        except Exception as exc:  # installed schema/reference fault
            self.report.configuration_error = True
            self.report.error(
                "SCHEMA_RESOLUTION_FAILED",
                f"Could not construct schema validator: {_bounded_message(str(exc))}",
                hint="Verify that every local $ref points to an installed canonical schema.",
            )
            return None
        self._schema_validators[key] = validator
        return validator

    def _validate_schema(self, document: MarkdownDocument, schemas: Mapping[str, dict[str, Any]]) -> None:
        artifact_type = _normalize_type(document.metadata.get("type"))
        if artifact_type is None or artifact_type not in TYPE_CONFIG:
            return
        schema = schemas.get(artifact_type)
        if schema is None:
            dashed = artifact_type.replace("_", "-")
            schema = schemas.get(dashed)
        if schema is None:
            self.report.error(
                "ARTIFACT_SCHEMA_MISSING",
                f"No schema is installed for artifact type '{artifact_type}'.",
                path=_relative(document.path, self.workspace),
                artifact_id=str(document.metadata.get("id", "")) or None,
                field="type",
                hint=f"Install the canonical {artifact_type.replace('_', '-')} schema.",
            )
            return
        validator = self._validator_for(artifact_type, schema, schemas)
        if validator is None:
            return
        try:
            errors = _actionable_schema_errors(validator.iter_errors(_json_value(document.metadata)))
        except Exception as exc:  # malformed resolution is an installed-schema fault
            self.report.error(
                "SCHEMA_RESOLUTION_FAILED",
                f"Could not resolve schema references: {exc}",
                path=_relative(document.path, self.workspace),
                hint="Verify that every local $ref points to an installed schema.",
            )
            return
        for error in errors:
            field_path = _schema_error_field(error)
            template_name = artifact_type.replace("_", "-")
            hint = (
                f"Correct '{field_path}' using templates/{template_name}.md and the canonical schema."
                if field_path
                else f"Update the artifact using templates/{template_name}.md and the canonical schema."
            )
            self.report.error(
                "SCHEMA_VALIDATION_FAILED",
                _safe_schema_message(error),
                path=_relative(document.path, self.workspace),
                artifact_id=str(document.metadata.get("id", "")) or None,
                field=field_path,
                hint=hint,
            )

    def _validate_envelope(self, document: MarkdownDocument) -> None:
        metadata = document.metadata
        path = _relative(document.path, self.workspace)
        required = ("schema_version", "id", "type", "title", "relationships")
        for field_name in required:
            if field_name not in metadata:
                self.report.error(
                    "REQUIRED_FIELD_MISSING",
                    f"Required common field '{field_name}' is missing.",
                    path=path,
                    artifact_id=str(metadata.get("id", "")) or None,
                    field=field_name,
                    hint=f"Add '{field_name}' to YAML frontmatter.",
                )
        artifact_type = _normalize_type(metadata.get("type"))
        if artifact_type not in TYPE_CONFIG:
            self.report.error(
                "ARTIFACT_TYPE_UNKNOWN",
                f"Unsupported artifact type: {metadata.get('type')!r}.",
                path=path,
                field="type",
                hint=f"Use one of: {', '.join(TYPE_CONFIG)}.",
            )
            return
        artifact_id = metadata.get("id")
        prefix, directory = TYPE_CONFIG[artifact_type]
        if not isinstance(artifact_id, str) or not INTERNAL_ID_RE.fullmatch(artifact_id):
            self.report.error(
                "ARTIFACT_ID_INVALID",
                "Artifact ID must use a supported typed prefix followed by "
                "8–32 uppercase Crockford Base32 characters.",
                path=path,
                field="id",
                hint=f"Use an ID such as {prefix}01JEXAMP1.",
            )
        elif not artifact_id.startswith(prefix):
            self.report.error(
                "ID_TYPE_MISMATCH",
                f"Type '{artifact_type}' requires ID prefix '{prefix}', found '{artifact_id}'.",
                path=path,
                artifact_id=artifact_id,
                field="id",
                hint=f"Change the ID prefix to '{prefix}' or correct the artifact type.",
            )
        parts = document.path.relative_to(self.workspace).parts
        if len(parts) < 3 or parts[0] != "product" or parts[1] != directory:
            self.report.error(
                "DIRECTORY_TYPE_MISMATCH",
                f"Type '{artifact_type}' belongs in product/{directory}/.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field="type",
                hint=f"Move this file to product/{directory}/ or correct its type.",
            )

    def _index_ids(self) -> None:
        for document in self.documents:
            artifact_id = document.metadata.get("id")
            if not isinstance(artifact_id, str) or not INTERNAL_ID_RE.fullmatch(artifact_id):
                continue
            if artifact_id in self.by_id:
                first = _relative(self.by_id[artifact_id].path, self.workspace)
                self.report.error(
                    "DUPLICATE_ARTIFACT_ID",
                    f"Artifact ID '{artifact_id}' is already used by {first}.",
                    path=_relative(document.path, self.workspace),
                    artifact_id=artifact_id,
                    field="id",
                    hint="Assign a new stable ID to one artifact and update its inbound relationships.",
                )
            else:
                self.by_id[artifact_id] = document

    def _relationship_ids(self, document: MarkdownDocument) -> Iterator[tuple[str, str]]:
        relationships = document.metadata.get("relationships")
        path = _relative(document.path, self.workspace)
        artifact_id = document.metadata.get("id")
        if not isinstance(relationships, Mapping):
            self.report.error(
                "RELATIONSHIPS_MALFORMED",
                "Relationships must be an object of named keys to an artifact ID or array of artifact IDs.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field="relationships",
                hint="Use relationships: {signals: [signal_...], opportunity: opportunity_...}.",
            )
            return
        for relation, value in relationships.items():
            values = value if isinstance(value, list) else [value]
            if isinstance(value, Mapping) or not isinstance(value, (str, list)):
                self.report.error(
                    "RELATIONSHIP_VALUE_MALFORMED",
                    f"Relationship '{relation}' must contain an artifact ID or array of IDs.",
                    path=path,
                    artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                    field=f"relationships.{relation}",
                    hint="External provider references belong in dedicated structured fields, not relationships.",
                )
                continue
            if isinstance(value, list) and not value:
                continue
            for index, target in enumerate(values):
                field_name = f"relationships.{relation}" + (f".{index}" if isinstance(value, list) else "")
                if not isinstance(target, str) or not INTERNAL_ID_RE.fullmatch(target):
                    self.report.error(
                        "RELATIONSHIP_ID_INVALID",
                        f"Relationship '{relation}' contains a malformed internal artifact ID.",
                        path=path,
                        artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                        field=field_name,
                        hint="Use a stable typed artifact ID; move URLs and provider objects to external reference fields.",
                    )
                    continue
                yield field_name, target

    def _validate_relationships(self) -> None:
        for document in self.documents:
            source_id = document.metadata.get("id")
            for field_name, target in self._relationship_ids(document):
                relation_name = field_name.split(".")[1] if "." in field_name else ""
                expected_prefix = RELATIONSHIP_TARGETS.get(relation_name)
                if expected_prefix and not target.startswith(expected_prefix):
                    self.report.error(
                        "RELATIONSHIP_TYPE_MISMATCH",
                        f"Relationship '{relation_name}' expects an ID beginning with '{expected_prefix}', found '{target}'.",
                        path=_relative(document.path, self.workspace),
                        artifact_id=source_id if isinstance(source_id, str) else None,
                        field=field_name,
                        hint=f"Use a {expected_prefix} artifact ID or correct the relationship key.",
                    )
                if target not in self.by_id:
                    self.report.error(
                        "BROKEN_INTERNAL_REFERENCE",
                        f"Relationship target '{target}' does not exist in this workspace.",
                        path=_relative(document.path, self.workspace),
                        artifact_id=source_id if isinstance(source_id, str) else None,
                        field=field_name,
                        hint="Add the referenced artifact or correct/remove the relationship ID.",
                    )
                    continue
                target_type = _normalize_type(self.by_id[target].metadata.get("type"))
                prefix_type = next((kind for prefix, kind in PREFIX_TO_TYPE.items() if target.startswith(prefix)), None)
                if target_type != prefix_type:
                    self.report.error(
                        "REFERENCE_TYPE_MISMATCH",
                        f"Target '{target}' declares type '{target_type}' but its ID prefix indicates '{prefix_type}'.",
                        path=_relative(document.path, self.workspace),
                        artifact_id=source_id if isinstance(source_id, str) else None,
                        field=field_name,
                        hint="Correct the target artifact type or typed ID prefix.",
                    )

    def _validate_reference(
        self,
        document: MarkdownDocument,
        field_name: str,
        target: Any,
        allowed_prefixes: tuple[str, ...],
    ) -> bool:
        artifact_id = document.metadata.get("id")
        path = _relative(document.path, self.workspace)
        if not isinstance(target, str) or not INTERNAL_ID_RE.fullmatch(target):
            self.report.error(
                "TYPED_REFERENCE_INVALID",
                f"Field '{field_name}' must contain a stable internal artifact ID.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field=field_name,
                hint=f"Use an ID beginning with one of: {', '.join(allowed_prefixes)}.",
            )
            return False
        if not target.startswith(allowed_prefixes):
            self.report.error(
                "TYPED_REFERENCE_PREFIX_MISMATCH",
                f"Field '{field_name}' does not accept ID '{target}'.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field=field_name,
                hint=f"Reference an artifact beginning with one of: {', '.join(allowed_prefixes)}.",
            )
            return False
        if target not in self.by_id:
            self.report.error(
                "BROKEN_TYPED_REFERENCE",
                f"Typed reference target '{target}' does not exist in this workspace.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field=field_name,
                hint="Add the referenced artifact or correct this stable ID.",
            )
            return False
        return True

    def _values(self, value: Any) -> list[Any]:
        return value if isinstance(value, list) else [value]

    def _relationship_values(self, metadata: Mapping[str, Any], *keys: str) -> set[str] | None:
        relationships = metadata.get("relationships")
        if not isinstance(relationships, Mapping):
            return None
        present = False
        values: set[str] = set()
        for key in keys:
            if key not in relationships:
                continue
            present = True
            raw = relationships[key]
            for value in self._values(raw):
                if isinstance(value, str):
                    values.add(value)
        return values if present else None

    def _check_relationship_consistency(
        self,
        document: MarkdownDocument,
        field_name: str,
        typed_values: Iterable[str],
        relation_keys: tuple[str, ...],
        prefix: str,
    ) -> None:
        related = self._relationship_values(document.metadata, *relation_keys)
        if related is None:
            return
        typed = {value for value in typed_values if value.startswith(prefix)}
        related = {value for value in related if value.startswith(prefix)}
        if typed != related:
            self.report.error(
                "REFERENCE_RELATIONSHIP_CONTRADICTION",
                f"Field '{field_name}' and relationships.{relation_keys[-1]} disagree: {sorted(typed)} != {sorted(related)}.",
                path=_relative(document.path, self.workspace),
                artifact_id=str(document.metadata.get("id", "")) or None,
                field=field_name,
                hint="Use the same stable IDs in the typed field and its equivalent relationship entry.",
            )

    def _validate_typed_references(self) -> None:
        scalar_specs: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
            ("opportunity_id", ("opportunity_",), ("opportunity", "opportunities")),
            ("initiative_id", ("initiative_",), ("initiative", "initiatives")),
            ("product_bet_id", ("initiative_", "prd_"), ("initiative", "initiatives", "prd", "prds")),
            ("outcome_contract_id", ("outcome_",), ("outcome_contract", "outcome_contracts")),
        )
        list_specs: tuple[tuple[str, tuple[str, ...]], ...] = (
            ("evidence_ids", ("signal_", "pattern_", "opportunity_")),
            ("supporting_signal_ids", ("signal_",)),
            ("contradictory_signal_ids", ("signal_",)),
            ("child_prd_ids", ("prd_",)),
            ("owner_artifact_ids", ("initiative_", "prd_")),
            ("product_bet_ids", ("initiative_", "prd_")),
            ("learnings", ("learning_",)),
        )
        consistency_by_field: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
            "evidence_ids": (
                ("signal_", ("signal", "signals")),
                ("pattern_", ("pattern", "patterns")),
                ("opportunity_", ("opportunity", "opportunities")),
            ),
            "child_prd_ids": (("prd_", ("prd", "prds")),),
            "owner_artifact_ids": (
                ("initiative_", ("initiative", "initiatives")),
                ("prd_", ("prd", "prds")),
            ),
            "product_bet_ids": (
                ("initiative_", ("initiative", "initiatives")),
                ("prd_", ("prd", "prds")),
            ),
            "learnings": (("learning_", ("learning", "learnings")),),
        }
        for document in self.documents:
            metadata = document.metadata
            for field_name, prefixes, relation_keys in scalar_specs:
                if field_name not in metadata:
                    continue
                value = metadata[field_name]
                self._validate_reference(document, field_name, value, prefixes)
                if isinstance(value, str):
                    for prefix in prefixes:
                        if value.startswith(prefix):
                            matching_keys = tuple(key for key in relation_keys if key.startswith(PREFIX_TO_TYPE[prefix].split("_")[0]))
                            self._check_relationship_consistency(
                                document, field_name, [value], matching_keys or relation_keys, prefix
                            )
                            break
            for field_name, prefixes in list_specs:
                if field_name not in metadata:
                    continue
                raw = metadata[field_name]
                effective_prefixes = prefixes
                if field_name == "evidence_ids" and _normalize_type(metadata.get("type")) == "opportunity":
                    effective_prefixes = ("signal_", "pattern_")
                if not isinstance(raw, list):
                    self.report.error(
                        "TYPED_REFERENCE_CONTAINER_INVALID",
                        f"Field '{field_name}' must be an array of stable artifact IDs.",
                        path=_relative(document.path, self.workspace),
                        artifact_id=str(metadata.get("id", "")) or None,
                        field=field_name,
                        hint="Use a YAML array, even when only one artifact is referenced.",
                    )
                    continue
                for index, value in enumerate(raw):
                    self._validate_reference(document, f"{field_name}.{index}", value, effective_prefixes)
                strings = [value for value in raw if isinstance(value, str)]
                for prefix, relation_keys in consistency_by_field.get(field_name, ()):
                    if (
                        field_name == "evidence_ids"
                        and prefix == "opportunity_"
                        and not any(value.startswith(prefix) for value in strings)
                        and "opportunity_id" in metadata
                    ):
                        # The owning Opportunity is also a navigation relationship;
                        # it need not be repeated in a PRD's evidence set.
                        continue
                    self._check_relationship_consistency(document, field_name, strings, relation_keys, prefix)

            pattern_signal_fields = ("supporting_signal_ids", "contradictory_signal_ids")
            if any(field_name in metadata for field_name in pattern_signal_fields):
                pattern_signals = {
                    value
                    for field_name in pattern_signal_fields
                    for value in (metadata.get(field_name) if isinstance(metadata.get(field_name), list) else [])
                    if isinstance(value, str)
                }
                self._check_relationship_consistency(
                    document,
                    "supporting_signal_ids+contradictory_signal_ids",
                    pattern_signals,
                    ("signal", "signals"),
                    "signal_",
                )

            outcome_ref = metadata.get("outcome_contract_ref")
            if outcome_ref is not None:
                if not isinstance(outcome_ref, Mapping):
                    self.report.error(
                        "OUTCOME_CONTRACT_REF_INVALID",
                        "outcome_contract_ref must be a structured object.",
                        path=_relative(document.path, self.workspace),
                        artifact_id=str(metadata.get("id", "")) or None,
                        field="outcome_contract_ref",
                        hint="Provide owner_artifact_id and extracted_artifact_id stable IDs.",
                    )
                else:
                    owner = outcome_ref.get("owner_artifact_id")
                    extracted = outcome_ref.get("extracted_artifact_id")
                    self._validate_reference(
                        document, "outcome_contract_ref.owner_artifact_id", owner, ("initiative_", "prd_")
                    )
                    if extracted is not None:
                        self._validate_reference(
                            document, "outcome_contract_ref.extracted_artifact_id", extracted, ("outcome_",)
                        )
                    if isinstance(owner, str):
                        prefix = "initiative_" if owner.startswith("initiative_") else "prd_"
                        keys = ("initiative", "initiatives") if prefix == "initiative_" else ("prd", "prds")
                        self._check_relationship_consistency(
                            document, "outcome_contract_ref.owner_artifact_id", [owner], keys, prefix
                        )
                    if isinstance(extracted, str):
                        self._check_relationship_consistency(
                            document,
                            "outcome_contract_ref.extracted_artifact_id",
                            [extracted],
                            ("outcome_contract", "outcome_contracts"),
                            "outcome_",
                        )
            if _normalize_type(metadata.get("type")) == "product_update":
                self._validate_update_sources(document)

    def _validate_product_graph_contracts(self) -> None:
        for document in self.documents:
            metadata = document.metadata
            artifact_type = _normalize_type(metadata.get("type"))
            legacy_fields = {"outcome", "outcome_contract", "problem", "product_thesis", "child_prd_ids"}
            if artifact_type not in {"prd", "initiative"} or legacy_fields.intersection(metadata):
                continue
            relationships = metadata.get("relationships")
            if not isinstance(relationships, Mapping):
                continue
            path = _relative(document.path, self.workspace)
            artifact_id = metadata.get("id")
            if artifact_type == "initiative":
                child_ids = relationships.get("prds")
                if not isinstance(child_ids, list) or len(child_ids) < 2:
                    self.report.error(
                        "INITIATIVE_CHILDREN_INCOMPLETE",
                        "An Initiative requires at least two distinct child PRDs; otherwise use a standalone PRD.",
                        path=path,
                        artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                        field="relationships.prds",
                        hint="Link at least two real child PRDs or remove the unnecessary Initiative.",
                    )
                    continue
                for child_id in child_ids:
                    child = self.by_id.get(child_id) if isinstance(child_id, str) else None
                    if child is None or _normalize_type(child.metadata.get("type")) != "prd":
                        continue
                    child_relationships = child.metadata.get("relationships")
                    back_reference = (
                        child_relationships.get("initiative")
                        if isinstance(child_relationships, Mapping)
                        else None
                    )
                    if back_reference != artifact_id:
                        self.report.error(
                            "INITIATIVE_PRD_LINK_NOT_BIDIRECTIONAL",
                            f"Child PRD '{child_id}' does not point back to Initiative '{artifact_id}'.",
                            path=_relative(child.path, self.workspace),
                            artifact_id=child_id,
                            field="relationships.initiative",
                            hint="Keep Initiative and child PRD relationships bidirectional.",
                        )
            elif artifact_type == "prd":
                initiative_id = relationships.get("initiative")
                opportunity_id = relationships.get("opportunity")
                if not isinstance(initiative_id, str) and not isinstance(opportunity_id, str):
                    self.report.error(
                        "PRD_PRODUCT_BET_LINK_MISSING",
                        "A PRD must link either to its parent Initiative or directly to its Opportunity.",
                        path=path,
                        artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                        field="relationships",
                        hint="Use relationships.initiative for a child PRD or relationships.opportunity for a standalone Product Bet.",
                    )
                if isinstance(initiative_id, str):
                    parent = self.by_id.get(initiative_id)
                    parent_relationships = parent.metadata.get("relationships") if parent else None
                    parent_children = (
                        parent_relationships.get("prds")
                        if isinstance(parent_relationships, Mapping)
                        else None
                    )
                    if parent is not None and (
                        not isinstance(parent_children, list) or artifact_id not in parent_children
                    ):
                        self.report.error(
                            "PRD_INITIATIVE_LINK_NOT_BIDIRECTIONAL",
                            f"Parent Initiative '{initiative_id}' does not list PRD '{artifact_id}'.",
                            path=_relative(parent.path, self.workspace),
                            artifact_id=initiative_id,
                            field="relationships.prds",
                            hint="Keep Initiative and child PRD relationships bidirectional.",
                        )

    def _validate_readable_document_contract(self, document: MarkdownDocument) -> None:
        metadata = document.metadata
        artifact_type = _normalize_type(metadata.get("type"))
        legacy_fields = {"outcome", "outcome_contract", "problem", "product_thesis", "child_prd_ids"}
        if legacy_fields.intersection(metadata):
            return  # backward-compatible large-frontmatter artifact
        required_sections = {
            "prd": (
                "problem",
                "evidence",
                "jtbd",
                "current and desired journey",
                "scope",
                "outcome contract",
                "gtm hypothesis",
                "risks and dependencies",
                "open questions",
                "delivery",
            ),
            "initiative": (
                "vision",
                "why this matters",
                "evidence and confidence",
                "shared outcome",
                "child prds",
                "sequencing and dependencies",
                "outcome contract",
                "gtm hypothesis",
                "risks and open questions",
            ),
        }.get(artifact_type, ())
        sections = markdown_sections(document)
        path = _relative(document.path, self.workspace)
        artifact_id = metadata.get("id")
        title_match = re.search(r"(?m)^#[ \t]+([^#\n].*?)[ \t]*$", document.body)
        expected_title = metadata.get("title")
        if (
            title_match is None
            or not isinstance(expected_title, str)
            or title_match.group(1).strip() != expected_title
        ):
            self.report.error(
                "READABLE_TITLE_MISMATCH",
                "The readable H1 must match the frontmatter title used for indexing.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field="body.h1",
                hint="Keep one H1 equal to the artifact title.",
            )
        for section_name in required_sections:
            content = sections.get(section_name, "").strip()
            if not content or re.search(r"<[^>\n]+>", content):
                self.report.error(
                    "READABLE_SECTION_MISSING",
                    f"Readable {artifact_type} section '## {section_name.title()}' is missing or empty.",
                    path=path,
                    artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                    field=f"body.{section_name}",
                    hint="Keep product reasoning in readable Markdown; an explicit named gap is valid, an empty section is not.",
                )
        if artifact_type == "prd":
            problem = sections.get("problem", "")
            if not re.search(
                r"(?mi)^\*\*(?:why now(?:\s*/\s*business reality)?|business reality):\*\*[ \t]*(?:\r?\n[ \t]*)?\S",
                problem,
            ):
                self.report.error(
                    "READABLE_SECTION_MISSING",
                    "PRD Problem requires a compact, explicit 'Why now / business reality' statement.",
                    path=path,
                    artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                    field="body.problem.why_now",
                    hint="State the concrete product or business trigger, or name the timing gap without inventing urgency.",
                )
            scope = sections.get("scope", "")
            for subsection in ("Requirements", "Non-goals"):
                if not re.search(rf"(?mi)^###[ \t]+{re.escape(subsection)}[ \t]*$", scope):
                    self.report.error(
                        "READABLE_SECTION_MISSING",
                        f"PRD Scope requires a '### {subsection}' subsection.",
                        path=path,
                        artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                        field=f"body.scope.{subsection.casefold()}",
                        hint="State the product boundary in readable Markdown.",
                    )

    def _validate_update_sources(self, document: MarkdownDocument) -> None:
        claims = document.metadata.get("claims")
        if not isinstance(claims, list):
            return
        for claim_index, claim in enumerate(claims):
            if not isinstance(claim, Mapping):
                continue
            references = claim.get("source_references")
            if not isinstance(references, list):
                continue
            for reference_index, reference in enumerate(references):
                field_name = f"claims.{claim_index}.source_references.{reference_index}"
                candidate: Any = None
                explicitly_internal = False
                if isinstance(reference, str):
                    candidate = reference.split("@", 1)[0]
                    explicitly_internal = bool(INTERNAL_ID_RE.fullmatch(candidate))
                elif isinstance(reference, Mapping):
                    kind = str(reference.get("type") or reference.get("kind") or reference.get("source_type") or "")
                    candidate = reference.get("artifact_id")
                    if candidate is None and kind in {"artifact", "internal", "product_artifact"}:
                        candidate = reference.get("id") or reference.get("reference")
                    if isinstance(candidate, str):
                        candidate = candidate.split("@", 1)[0]
                    explicitly_internal = kind in {"artifact", "internal", "product_artifact"} or "artifact_id" in reference
                if explicitly_internal:
                    self._validate_reference(
                        document,
                        field_name,
                        candidate,
                        tuple(PREFIX_TO_TYPE),
                    )

    def _current_decision_events(self) -> dict[str, tuple[MarkdownDocument, list[Mapping[str, Any]]]]:
        result: dict[str, tuple[MarkdownDocument, list[Mapping[str, Any]]]] = {}
        seen_event_ids: dict[str, str] = {}
        for document in self.documents:
            artifact_id = document.metadata.get("id")
            raw = document.metadata.get("decision_events")
            if raw is None:
                continue
            if not isinstance(raw, list):
                continue  # canonical schema reports the container error
            events: list[Mapping[str, Any]] = []
            local_ids: set[str] = set()
            for index, event in enumerate(raw):
                if not isinstance(event, Mapping):
                    continue
                event_id = event.get("id")
                field_name = f"decision_events.{index}.id"
                if not isinstance(event_id, str) or not event_id.startswith("decision_"):
                    continue
                if event_id in local_ids or event_id in seen_event_ids:
                    self.report.error(
                        "DUPLICATE_DECISION_EVENT_ID",
                        f"Decision event ID '{event_id}' is already used by {seen_event_ids.get(event_id, artifact_id)}.",
                        path=_relative(document.path, self.workspace),
                        artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                        field=field_name,
                        hint="Assign a new immutable decision event ID.",
                    )
                local_ids.add(event_id)
                seen_event_ids[event_id] = str(artifact_id)
                if self.command == "smoke-test" and self._git_commit_available():
                    based_on = event.get("based_on_version")
                    reachable = False
                    if isinstance(based_on, str) and re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", based_on):
                        if self._fixture_synthetic_mode():
                            reachable = True
                        else:
                            try:
                                git_result = self._git("rev-parse", "--verify", f"{based_on}^{{commit}}")
                                reachable = git_result.returncode == 0 and git_result.stdout.strip().lower() == based_on.lower()
                            except (OSError, UnicodeError, subprocess.SubprocessError):
                                reachable = False
                    if not reachable:
                        self.report.error(
                            "DECISION_EVENT_VERSION_UNVERIFIED",
                            "Decision event based_on_version must be a reachable full commit SHA for smoke validation.",
                            path=_relative(document.path, self.workspace),
                            artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                            field=f"decision_events.{index}.based_on_version",
                            hint="Record the full commit SHA containing the reviewed decision basis.",
                        )
                    elif not self._fixture_synthetic_mode() and not self._artifact_exists_at_commit(
                        _relative(document.path, self.workspace), based_on
                    ):
                        self.report.error(
                            "DECISION_EVENT_BASIS_ARTIFACT_MISSING",
                            "Decision event based_on_version is reachable but does not contain this artifact.",
                            path=_relative(document.path, self.workspace),
                            artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                            field=f"decision_events.{index}.based_on_version",
                            hint="Commit the undecided artifact first, then bind the human decision to that exact commit.",
                        )
                events.append(event)
            prior_ids: set[str] = set()
            for index, event in enumerate(events):
                supersedes = event.get("supersedes")
                if supersedes is not None and supersedes not in prior_ids:
                    self.report.error(
                        "DECISION_EVENT_SUPERSEDES_INVALID",
                        f"Decision event supersedes unknown, self, or later event '{supersedes}'.",
                        path=_relative(document.path, self.workspace),
                        artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                        field=f"decision_events.{index}.supersedes",
                        hint="A correction must append a new event that supersedes an existing event in the same artifact.",
                    )
                event_id = event.get("id")
                if isinstance(event_id, str):
                    prior_ids.add(event_id)
            if isinstance(artifact_id, str):
                result[artifact_id] = (document, events)
        return result

    def _git_commit_available(self) -> bool:
        try:
            result = self._git("rev-parse", "--verify", "HEAD^{commit}")
        except (OSError, UnicodeError, subprocess.SubprocessError):
            return False
        return result.returncode == 0

    def _artifact_exists_at_commit(self, relative_path: str, commit: str) -> bool:
        try:
            root_result = self._git("rev-parse", "--show-toplevel")
        except (OSError, UnicodeError, subprocess.SubprocessError):
            return False
        if root_result.returncode != 0:
            return False
        try:
            repository_root = Path(root_result.stdout.strip()).resolve()
            artifact_path = (self.workspace / relative_path).resolve()
            repository_path = artifact_path.relative_to(repository_root).as_posix()
        except (OSError, ValueError):
            return False
        try:
            result = self._git("cat-file", "-e", f"{commit}:{repository_path}")
        except (OSError, UnicodeError, subprocess.SubprocessError):
            return False
        return result.returncode == 0

    def _fixture_synthetic_mode(self) -> bool:
        if self._fixture_synthetic_cache is not None:
            return self._fixture_synthetic_cache
        self._fixture_synthetic_cache = False
        distribution_root = self._distribution_root()
        fixture_roots = (
            distribution_root / "tests" / "fixtures",
            distribution_root / "examples" / "fixtures",  # legacy distributions
        ) if distribution_root else ()
        state_path = self.workspace / ".product-os" / "review-state.yaml"
        if not any(self._safe_contained_path(self.workspace, root) for root in fixture_roots):
            return False
        if not state_path.is_file() or not self._safe_contained_path(state_path, self.workspace):
            return False
        try:
            state = load_yaml_strict(state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError, yaml.YAMLError):
            return False
        if not isinstance(state, Mapping):
            return False
        containers = [
            value for key, value in state.items()
            if key in {"artifacts", "approved_artifacts", "reviews", "approval_state"} and isinstance(value, Mapping)
        ]
        self._fixture_synthetic_cache = any(
            isinstance(entry, Mapping) and entry.get("synthetic") is True
            for container in containers
            for entry in container.values()
        )
        return self._fixture_synthetic_cache

    def _configured_base_ref(self) -> str | None:
        if self.base_ref:
            self._base_ref_source = "explicit"
            return self.base_ref
        git_config = self.config.get("git") if isinstance(self.config.get("git"), Mapping) else {}
        validation = self.config.get("validation") if isinstance(self.config.get("validation"), Mapping) else {}
        for value in (validation.get("base_ref"), git_config.get("base_ref"), self.config.get("base_ref")):
            if isinstance(value, str) and value.strip():
                self._base_ref_source = "explicit"
                return value.strip()
        for value in (git_config.get("default_branch"), self.config.get("default_branch")):
            if isinstance(value, str) and value.strip():
                self._base_ref_source = "default_branch"
                return value.strip()
        self._base_ref_source = "implicit_head"
        return "HEAD"

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.workspace), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def _baseline_decision_events(self, base_ref: str) -> dict[str, tuple[str, list[Mapping[str, Any]]]] | None:
        try:
            root_result = self._git("rev-parse", "--show-toplevel")
            verify = self._git("rev-parse", "--verify", "--end-of-options", f"{base_ref}^{{commit}}")
        except (OSError, UnicodeError, subprocess.SubprocessError) as exc:
            self._baseline_error("DECISION_BASELINE_READ_FAILED", f"Git baseline lookup failed: {exc}")
            return None
        if root_result.returncode != 0:
            return None
        if verify.returncode != 0:
            if self._repository_has_prior_commit():
                self._baseline_error(
                    "DECISION_BASELINE_UNAVAILABLE",
                    f"Configured baseline ref '{base_ref}' is not reachable in a repository with prior history.",
                )
            return None
        commit = verify.stdout.strip()
        if not re.fullmatch(r"[0-9a-fA-F]{40,64}", commit):
            self._baseline_error("DECISION_BASELINE_READ_FAILED", "Git returned an invalid baseline commit ID.")
            return None
        if self._base_ref_source in {"default_branch", "implicit_head"}:
            try:
                head = self._git("rev-parse", "--verify", "HEAD^{commit}")
            except (OSError, UnicodeError, subprocess.SubprocessError) as exc:
                self._baseline_error("DECISION_BASELINE_READ_FAILED", f"Could not resolve current Git commit: {exc}")
                return None
            if head.returncode != 0:
                self._baseline_error("DECISION_BASELINE_READ_FAILED", "Could not resolve current Git commit.")
                return None
            head_commit = head.stdout.strip()
            if self._base_ref_source == "default_branch":
                try:
                    merge_base = self._git("merge-base", head_commit, commit)
                except (OSError, UnicodeError, subprocess.SubprocessError) as exc:
                    self._baseline_error("DECISION_BASELINE_READ_FAILED", f"Could not resolve default-branch merge-base: {exc}")
                    return None
                if merge_base.returncode != 0 or not re.fullmatch(r"[0-9a-fA-F]{40,64}", merge_base.stdout.strip()):
                    self._baseline_error(
                        "DECISION_BASELINE_UNAVAILABLE",
                        f"Configured default branch '{base_ref}' has no trustworthy merge-base with HEAD.",
                    )
                    return None
                commit = merge_base.stdout.strip()
            if head_commit.lower() == commit.lower():
                try:
                    parent = self._git("rev-parse", "--verify", f"{commit}^")
                except (OSError, UnicodeError, subprocess.SubprocessError) as exc:
                    self._baseline_error("DECISION_BASELINE_PARENT_UNAVAILABLE", f"Could not resolve baseline parent: {exc}")
                    return None
                if parent.returncode != 0 or not re.fullmatch(r"[0-9a-fA-F]{40,64}", parent.stdout.strip()):
                    if self._repository_has_prior_commit():
                        self._baseline_error(
                            "DECISION_BASELINE_PARENT_UNAVAILABLE",
                            f"Configured default branch '{base_ref}' points at the current commit and has no resolvable parent.",
                        )
                        return None
                    self.report.warning(
                        "DECISION_BASELINE_UNAVAILABLE",
                        f"Configured default branch '{base_ref}' is the repository's root commit; there is no earlier decision baseline to compare.",
                        hint="Append-only comparison starts after the next commit; decision based_on_version values are still checked now.",
                    )
                    return {}
                commit = parent.stdout.strip()
        self.resolved_base_sha = commit.lower()
        git_root = Path(root_result.stdout.strip()).resolve()
        try:
            workspace_prefix = self.workspace.relative_to(git_root).as_posix()
        except ValueError:
            self._baseline_error("DECISION_BASELINE_READ_FAILED", "Workspace is outside the resolved Git repository.")
            return None
        product_path = "product" if workspace_prefix == "." else f"{workspace_prefix}/product"
        listing = self._git("ls-tree", "-r", "--name-only", commit, "--", product_path)
        if listing.returncode != 0:
            self._baseline_error("DECISION_BASELINE_READ_FAILED", "Could not list artifacts at the resolved baseline commit.")
            return None
        baseline: dict[str, tuple[str, list[Mapping[str, Any]]]] = {}
        for repo_path in listing.stdout.splitlines():
            if not repo_path.endswith(".md"):
                continue
            shown = self._git("show", f"{commit}:{repo_path}")
            if shown.returncode != 0:
                self._baseline_error("DECISION_BASELINE_READ_FAILED", f"Could not read baseline artifact '{repo_path}'.")
                return None
            try:
                document = parse_markdown_text(shown.stdout, path=Path(repo_path))
            except FrontmatterError as exc:
                self._baseline_error(
                    "DECISION_BASELINE_PARSE_FAILED",
                    f"Cannot parse baseline artifact '{repo_path}': {_bounded_message(str(exc))}",
                )
                continue
            artifact_id = document.metadata.get("id")
            raw_events = document.metadata.get("decision_events")
            if isinstance(artifact_id, str) and isinstance(raw_events, list):
                events = [event for event in raw_events if isinstance(event, Mapping)]
                baseline[artifact_id] = (repo_path, events)
        return baseline

    def _repository_has_prior_commit(self) -> bool:
        try:
            result = self._git("rev-list", "--count", "HEAD")
        except (OSError, UnicodeError, subprocess.SubprocessError):
            return False
        if result.returncode != 0:
            return False
        try:
            return int(result.stdout.strip()) >= 2
        except ValueError:
            return False

    def _baseline_error(self, code: str, message: str) -> None:
        self._baseline_failure_reported = True
        self.report.error(
            code,
            message,
            hint="Repair or fetch Git history, or pass an explicit reachable --base-ref.",
        )

    def _validate_decision_events(self) -> None:
        current = self._current_decision_events()
        base_ref = self._configured_base_ref() or "HEAD"
        baseline = self._baseline_decision_events(base_ref)
        if baseline is None:
            if self._repository_has_prior_commit() and not self._baseline_failure_reported:
                self._baseline_error(
                    "DECISION_BASELINE_UNAVAILABLE",
                    f"Could not resolve a trustworthy prior baseline from '{base_ref}' in a repository with history.",
                )
            elif current and not self._baseline_failure_reported:
                self.report.warning(
                    "DECISION_BASELINE_UNAVAILABLE",
                    f"Could not resolve Git baseline '{base_ref}'; append-only decision history was not compared.",
                    hint="Fetch or pass --base-ref with a reachable commit before approval or delivery handoff.",
                )
            return
        for artifact_id, (baseline_path, old_events) in baseline.items():
            if not old_events:
                continue
            current_entry = current.get(artifact_id)
            if current_entry is None:
                self.report.error(
                    "DECISION_EVENTS_REMOVED",
                    f"Artifact '{artifact_id}' with recorded decision events was removed since {base_ref}.",
                    path=baseline_path,
                    artifact_id=artifact_id,
                    field="decision_events",
                    hint="Restore the artifact/events; archive through Git without deleting immutable decision history.",
                )
                continue
            document, new_events = current_entry
            old_ids = [event.get("id") for event in old_events]
            new_ids = [event.get("id") for event in new_events]
            old_by_id = {event.get("id"): _json_value(event) for event in old_events if isinstance(event.get("id"), str)}
            new_by_id = {event.get("id"): _json_value(event) for event in new_events if isinstance(event.get("id"), str)}
            for event_id, old_payload in old_by_id.items():
                if event_id not in new_by_id:
                    self.report.error(
                        "DECISION_EVENT_REMOVED",
                        f"Previously recorded decision event '{event_id}' was removed.",
                        path=_relative(document.path, self.workspace),
                        artifact_id=artifact_id,
                        field="decision_events",
                        hint="Restore the event and append a superseding correction instead.",
                    )
                elif new_by_id[event_id] != old_payload:
                    self.report.error(
                        "DECISION_EVENT_MUTATED",
                        f"Previously recorded decision event '{event_id}' was modified.",
                        path=_relative(document.path, self.workspace),
                        artifact_id=artifact_id,
                        field="decision_events",
                        hint="Restore the immutable payload and append a new event with supersedes pointing to it.",
                    )
            if new_ids[: len(old_ids)] != old_ids:
                self.report.error(
                    "DECISION_EVENT_NOT_APPENDED",
                    "Decision events changed before the end of the previously recorded sequence.",
                    path=_relative(document.path, self.workspace),
                    artifact_id=artifact_id,
                    field="decision_events",
                    hint="Preserve the prior sequence exactly and add new events only at the end.",
                )

    def _configured_excerpt_limit(self) -> int:
        for key_path in (
            ("evidence", "max_excerpt_chars"),
            ("evidence", "excerpt_max_characters"),
            ("evidence_policy", "max_excerpt_chars"),
        ):
            value: Any = self.config
            for key in key_path:
                value = value.get(key) if isinstance(value, Mapping) else None
            if isinstance(value, int) and 1 <= value <= 500:
                return value
        return 500

    def _validate_evidence(self, document: MarkdownDocument) -> None:
        path = _relative(document.path, self.workspace)
        artifact_id = document.metadata.get("id")
        limit = self._configured_excerpt_limit()
        for field_path, value in _walk(document.metadata):
            if not field_path:
                continue
            field_name = field_path[-1].lower().replace("-", "_")
            dotted = ".".join(field_path)
            is_excerpt = field_name in {"excerpt", "evidence_excerpt", "approved_excerpt", "quote"}
            is_excerpt_text = field_name == "text" and len(field_path) >= 2 and field_path[-2].lower() in {
                "excerpt",
                "evidence_excerpt",
                "approved_excerpt",
            }
            if (is_excerpt or is_excerpt_text) and isinstance(value, str):
                if len(value) > limit:
                    self.report.error(
                        "EVIDENCE_EXCERPT_TOO_LONG",
                        f"Evidence excerpt is {len(value)} characters; the configured maximum is {limit}.",
                        path=path,
                        artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                        field=dotted,
                        hint="Keep only the minimal anonymized excerpt or use reference-only evidence.",
                    )
            if field_name in {"transcript", "raw_transcript", "full_transcript", "transcript_text"} and isinstance(value, str) and value.strip():
                self.report.error(
                    "TRANSCRIPT_CONTENT_FORBIDDEN",
                    "Transcript content must remain in the external source; Git may store only references and minimal excerpts.",
                    path=path,
                    artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                    field=dotted,
                    hint="Remove transcript text and retain provider, external_id, dates, fingerprint, and an optional <=500-character excerpt.",
                )
            elif isinstance(value, str) and len(value) >= 5_000 and len(SPEAKER_LINE_RE.findall(value)) >= 8:
                self.report.error(
                    "TRANSCRIPT_SIZED_CONTENT",
                    f"Field contains {len(value)} characters and repeated speaker turns, consistent with transcript-sized content.",
                    path=path,
                    artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                    field=dotted,
                    hint="Externalize the transcript and keep a source reference plus a minimal approved excerpt.",
                )
        if len(document.body) >= 5_000 and len(SPEAKER_LINE_RE.findall(document.body)) >= 8:
            self.report.error(
                "TRANSCRIPT_SIZED_CONTENT",
                f"Markdown body contains {len(document.body)} characters and repeated speaker turns, consistent with transcript-sized content.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field="body",
                hint="Externalize the transcript and keep only decision-relevant evidence in the product document.",
            )
        for label, pattern in CREDENTIAL_PATTERNS:
            if pattern.search(document.raw):
                self.report.error(
                    "CREDENTIAL_LIKE_CONTENT",
                    f"Detected credential-like content ({label}).",
                    path=path,
                    artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                    hint="Remove the secret, rotate it if real, and reference the configured provider connection instead.",
                )

    def _outcome_container(self, document: MarkdownDocument) -> Mapping[str, Any] | None:
        metadata = document.metadata
        legacy: Mapping[str, Any] | None = None
        for key in ("outcome", "outcome_contract"):
            value = metadata.get(key)
            if isinstance(value, Mapping):
                legacy = value
                break
        try:
            value = structured_blocks(document).get("outcome")
        except FrontmatterError as exc:
            self.report.error(
                "STRUCTURED_BLOCK_INVALID",
                str(exc),
                path=_relative(document.path, self.workspace),
                artifact_id=str(metadata.get("id", "")) or None,
                field="body.product-os:outcome",
                hint="Keep one valid YAML object in the named Outcome Contract block.",
            )
            return legacy
        if legacy is not None and isinstance(value, Mapping):
            self.report.error(
                "OUTCOME_CONTRACT_DUPLICATED",
                "Outcome Contract exists in both frontmatter and the Markdown body.",
                path=_relative(document.path, self.workspace),
                artifact_id=str(metadata.get("id", "")) or None,
                field="body.product-os:outcome",
                hint="Keep one canonical Outcome Contract; prefer the named block in the readable section.",
            )
            return legacy
        if legacy is not None:
            return legacy
        if isinstance(value, Mapping):
            return value
        return None

    def _validate_outcome(self, document: MarkdownDocument) -> None:
        metadata = document.metadata
        artifact_type = _normalize_type(metadata.get("type"))
        path = _relative(document.path, self.workspace)
        artifact_id = metadata.get("id")
        if artifact_type == "outcome_contract":
            found = self._outcome_container(document)
            if found is None and ("definition" in metadata or "binding" in metadata):
                # Validate legacy/invalid standalone shapes deeply enough to return the
                # actionable binding error in addition to the canonical schema error.
                found = metadata
            if found is None:
                self.report.error(
                    "OUTCOME_CONTRACT_MISSING",
                    "Standalone Outcome Contract requires an outcome object.",
                    path=path,
                    artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                    field="outcome",
                    hint="Add outcome.definition and outcome.binding.",
                )
                return
            outcome = found
        else:
            found = self._outcome_container(document)
            if found is None:
                relationships = metadata.get("relationships")
                linked = isinstance(relationships, Mapping) and bool(
                    relationships.get("outcome_contract") or relationships.get("outcome_contracts")
                )
                if linked:
                    return
                self.report.error(
                    "OUTCOME_CONTRACT_MISSING",
                    f"Every {artifact_type} Product Bet requires an embedded or linked Outcome Contract.",
                    path=path,
                    artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                    field="body.product-os:outcome",
                    hint="Add an Outcome Contract block to the Markdown body, or link an extracted Outcome Contract.",
                )
                return
            outcome = found
        schemas = self._load_schemas()
        common_schema = schemas.get("common")
        if isinstance(common_schema, Mapping) and isinstance(common_schema.get("$defs"), Mapping):
            outcome_schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$ref": "https://productdecisionos.org/schemas/common.schema.json#/$defs/outcomeContract",
            }
            outcome_validator = self._validator_for("structured-outcome", outcome_schema, schemas)
            if outcome_validator is not None:
                for error in _actionable_schema_errors(
                    outcome_validator.iter_errors(_json_value(outcome))
                ):
                    field_path = _schema_error_field(error)
                    self.report.error(
                        "OUTCOME_SCHEMA_INVALID",
                        _safe_schema_message(error),
                        path=path,
                        artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                        field=f"body.product-os:outcome.{field_path}" if field_path else "body.product-os:outcome",
                        hint="Correct the Outcome Contract using the canonical PRD or Initiative template.",
                    )
        definition = outcome.get("definition")
        if not isinstance(definition, Mapping):
            self.report.error(
                "OUTCOME_DEFINITION_MISSING",
                "Outcome Contract requires a structured measurement definition.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field="outcome.definition",
                hint="Define baseline/current state, target, method, slices, guardrails, window/review date, and decision rule.",
            )
        else:
            requirements = (
                (("baseline", "current_state"), "baseline or current state"),
                (("target", "target_outcome", "target_movement"), "target outcome"),
                (("method", "metric", "proof_method"), "measurement method"),
                (("slices",), "relevant slices (use [] only when explicitly not applicable)"),
                (("guardrails",), "guardrails (use [] only when explicitly not applicable)"),
                (("window", "review_date"), "window or review date"),
                (("decision_rule",), "decision rule"),
            )
            for names, label in requirements:
                if not _has(definition, *names):
                    self.report.error(
                        "OUTCOME_DEFINITION_INCOMPLETE",
                        f"Measurement definition is missing {label}.",
                        path=path,
                        artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                        field="outcome.definition",
                        hint=f"Add one of: {', '.join(names)}.",
                    )
        binding = outcome.get("binding")
        if not isinstance(binding, Mapping):
            self.report.error(
                "OUTCOME_BINDING_MISSING",
                "Outcome Contract requires a structured measurement binding.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field="outcome.binding",
                hint="Record status as unconfigured, planned, executable, or manual and add status-specific provenance.",
            )
            return
        status = binding.get("status")
        if status not in {"unconfigured", "planned", "executable", "manual"}:
            self.report.error(
                "OUTCOME_BINDING_STATUS_INVALID",
                f"Unknown measurement binding status: {status!r}.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field="outcome.binding.status",
                hint="Use unconfigured, planned, executable, or manual.",
            )
            return
        if status == "planned":
            for required in ("owner", "due_before"):
                if not _has(binding, required):
                    self.report.error(
                        "PLANNED_BINDING_NOT_READY",
                        f"Planned binding is missing '{required}', so delivery handoff is not ready.",
                        path=path,
                        artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                        field=f"outcome.binding.{required}",
                        hint="Assign an owner and a due date no later than release.",
                    )
        if status == "executable":
            reference_keys = ("query_reference", "case_set_reference", "metric_definition_reference", "review_reference")
            required_groups: tuple[tuple[tuple[str, ...], str], ...] = (
                (reference_keys, "query, case-set, metric-definition, or review reference"),
                (("definition_version",), "definition_version"),
                (("verified_by",), "verified_by"),
                (("verified_at",), "verified_at"),
            )
            for names, label in required_groups:
                if not _has(binding, *names):
                    self.report.error(
                        "EXECUTABLE_BINDING_UNVERIFIED",
                        f"Executable binding is missing {label}.",
                        path=path,
                        artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                        field="outcome.binding",
                        hint="Return the binding to planned or record the executable reference, definition version, verifier, and verification time.",
                    )
            current_definition_version = definition.get("version") if isinstance(definition, Mapping) else None
            if not current_definition_version:
                self.report.error(
                    "OUTCOME_DEFINITION_VERSION_MISSING",
                    "Executable binding requires a versioned outcome definition.",
                    path=path,
                    artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                    field="outcome.definition.version",
                    hint="Assign the definition version verified by the executable binding.",
                )
            elif binding.get("definition_version") != current_definition_version:
                self.report.error(
                    "OUTCOME_BINDING_STALE",
                    "Executable binding was verified against a different measurement definition version.",
                    path=path,
                    artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                    field="outcome.binding.definition_version",
                    hint="Set status to planned until the owner verifies the current definition.",
                )
        anchor = binding.get("measurement_anchor")
        if anchor is not None and (not isinstance(anchor, Mapping) or anchor.get("type") not in {"exposure_event", "release", "manual"}):
            self.report.error(
                "MEASUREMENT_ANCHOR_NOT_READY",
                "Measurement binding must declare an anchor type: exposure_event, release, or manual.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field="outcome.binding.measurement_anchor",
                hint="Declare how the observation window will start; record the actual reference when exposure, release, or evaluation occurs.",
            )
        ready_markers = {
            str(metadata.get("delivery_state", "")).lower(),
            str(metadata.get("lifecycle", "")).lower(),
            str(metadata.get("status", "")).lower(),
        }
        requires_actual_anchor = bool(
            ready_markers.intersection({"released", "delivered", "awaiting_measurement", "outcome_review", "learning_complete"})
            or metadata.get("outcome_review")
            or metadata.get("results")
        )
        if requires_actual_anchor and (not isinstance(anchor, Mapping) or not _has(anchor, "reference", "occurred_at", "recorded_at")):
            self.report.error(
                "MEASUREMENT_ANCHOR_MISSING",
                "Delivered or evaluation-ready work has no actual measurement anchor reference/time.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field="outcome.binding.measurement_anchor",
                hint="Record the actual exposure, verified release, or manual evaluation event before starting the measurement window.",
            )

    def _validate_learning_anchor(self, document: MarkdownDocument) -> None:
        metadata = document.metadata
        path = _relative(document.path, self.workspace)
        artifact_id = metadata.get("id")
        anchor = metadata.get("measurement_anchor")
        if not isinstance(anchor, Mapping):
            result = metadata.get("result") or metadata.get("results")
            anchor = result.get("measurement_anchor") if isinstance(result, Mapping) else None
        if not isinstance(anchor, Mapping) or anchor.get("type") not in {"exposure_event", "release", "manual"} or not _has(anchor, "reference", "occurred_at", "recorded_at"):
            self.report.error(
                "MEASUREMENT_ANCHOR_MISSING",
                "Learning must record the actual measurement anchor and its provenance.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field="measurement_anchor",
                hint="Record anchor type plus the actual reference or occurrence time used to start the observation window.",
            )

    def _validate_learning_versions(self, document: MarkdownDocument) -> None:
        metadata = document.metadata
        reference = metadata.get("outcome_contract_ref")
        if not isinstance(reference, Mapping):
            return
        owner_id = reference.get("owner_artifact_id")
        owner = self.by_id.get(owner_id) if isinstance(owner_id, str) else None
        if owner is None:
            return  # typed-reference validation reports missing/wrong owners
        outcome = self._outcome_container(owner)
        definition = outcome.get("definition") if isinstance(outcome, Mapping) else None
        owner_version = definition.get("version") if isinstance(definition, Mapping) else None
        if not isinstance(owner_version, str) or not owner_version:
            return  # owner readiness/schema checks report the missing definition version
        path = _relative(document.path, self.workspace)
        artifact_id = metadata.get("id")
        if reference.get("definition_version") != owner_version:
            self.report.error(
                "OUTCOME_CONTRACT_REF_STALE",
                f"Learning references definition version '{reference.get('definition_version')}', owner uses '{owner_version}'.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field="outcome_contract_ref.definition_version",
                hint="Re-evaluate the learning against the owner's current outcome definition.",
            )
        results = metadata.get("results")
        provenance = results.get("provenance") if isinstance(results, Mapping) else None
        if isinstance(provenance, Mapping) and provenance.get("definition_version") != owner_version:
            self.report.error(
                "RESULT_PROVENANCE_DEFINITION_STALE",
                f"Result provenance uses definition version '{provenance.get('definition_version')}', owner uses '{owner_version}'.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field="results.provenance.definition_version",
                hint="Re-run or re-import results using the owner's current outcome definition.",
            )

    def _current_prd_version(self, metadata: Mapping[str, Any], *, path: str) -> Any:
        artifact_id = metadata.get("id")
        review_state_path = self.workspace / ".product-os" / "review-state.yaml"
        if not isinstance(artifact_id, str) or not review_state_path.is_file():
            self.report.error(
                "IMPLEMENTATION_REVIEW_STATE_UNAVAILABLE",
                "Implementation references cannot be checked without .product-os/review-state.yaml.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field="implementation_refs",
                hint="Record the PRD's approved_version in canonical review state before handoff.",
            )
            return None
        if not self._safe_contained_path(review_state_path, self.workspace):
            self._report_unsafe_path(review_state_path, "review-state cache")
            return None
        try:
            state = load_yaml_strict(review_state_path.read_text(encoding="utf-8"))
            if not isinstance(state, Mapping):
                raise ValueError("review-state root must be an object")
        except (OSError, UnicodeError, ValueError, yaml.YAMLError):
            self.report.error(
                "IMPLEMENTATION_REVIEW_STATE_INVALID",
                "Cannot parse review state as a strict UTF-8 YAML object.",
                path=_relative(review_state_path, self.workspace),
                artifact_id=artifact_id,
                field="implementation_refs",
                hint="Restore a UTF-8 YAML object with an approved_version for this PRD.",
            )
            return None
        containers = [state]
        containers.extend(
            value for key, value in state.items()
            if key in {"artifacts", "approved_artifacts", "reviews", "approval_state"} and isinstance(value, Mapping)
        )
        selected_entry: Mapping[str, Any] | None = None
        for container in containers:
            entry = container.get(artifact_id) if isinstance(container, Mapping) else None
            if isinstance(entry, Mapping) and _has(entry, "approved_version"):
                selected_entry = entry
                break
        if selected_entry is not None:
            approved_version = selected_entry.get("approved_version")
            if selected_entry.get("synthetic") is True:
                distribution_root = self._distribution_root()
                fixture_roots = (
                    distribution_root / "tests" / "fixtures",
                    distribution_root / "examples" / "fixtures",  # legacy distributions
                ) if distribution_root else ()
                if (
                    any(self._safe_contained_path(self.workspace, root) for root in fixture_roots)
                    and isinstance(approved_version, str)
                    and re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", approved_version)
                ):
                    return approved_version
                self.report.error(
                    "IMPLEMENTATION_REVIEW_STATE_UNVERIFIED",
                    "Synthetic review-state provenance is accepted only inside this distribution's test fixtures.",
                    path=_relative(review_state_path, self.workspace),
                    artifact_id=artifact_id,
                    field="implementation_refs",
                )
                return approved_version
            provenance = selected_entry.get("provenance")
            verification_mode = provenance.get("verification_mode") if isinstance(provenance, Mapping) else None
            git_sha = provenance.get("git_sha") if isinstance(provenance, Mapping) else None
            common_ready = all(
                _has(selected_entry, key) for key in ("approved_by", "approved_at")
            ) and isinstance(provenance, Mapping) and all(
                _has(provenance, key) for key in ("git_sha", "verification_mode", "verified_by", "verified_at")
            )
            review = self.config.get("review") if isinstance(self.config.get("review"), Mapping) else {}
            solo = review.get("solo_approval") if isinstance(review.get("solo_approval"), Mapping) else {}
            mode_ready = (
                verification_mode == "provider_review"
                and review.get("mode") == "provider"
                and _has(provenance, "provider_reference")
            ) or (
                verification_mode == "solo_commit"
                and review.get("mode") == "solo"
                and solo.get("allowed") is True
                and provenance.get("commit_trailer_verified") is True
            )
            sha_ready = (
                isinstance(approved_version, str)
                and isinstance(git_sha, str)
                and approved_version.lower() == git_sha.lower()
                and re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", git_sha) is not None
            )
            reachable = False
            artifact_present = False
            if sha_ready:
                try:
                    resolved = self._git("rev-parse", "--verify", f"{git_sha}^{{commit}}")
                    reachable = resolved.returncode == 0 and resolved.stdout.strip().lower() == git_sha.lower()
                except (OSError, UnicodeError, subprocess.SubprocessError):
                    reachable = False
                if reachable:
                    artifact_present = self._artifact_exists_at_commit(path, git_sha)
            trailer_present = True
            if verification_mode == "solo_commit" and reachable:
                required_trailer = solo.get("commit_trailer")
                trailer_present = False
                if isinstance(required_trailer, str) and required_trailer.strip():
                    try:
                        message = self._git("show", "-s", "--format=%B", git_sha)
                        trailer_present = message.returncode == 0 and required_trailer.strip() in {
                            line.strip() for line in message.stdout.splitlines()
                        }
                    except (OSError, UnicodeError, subprocess.SubprocessError):
                        trailer_present = False
            if not (
                common_ready
                and mode_ready
                and sha_ready
                and reachable
                and artifact_present
                and trailer_present
            ):
                self.report.error(
                    "IMPLEMENTATION_REVIEW_STATE_UNVERIFIED",
                    "Review-state cache lacks complete provenance, the artifact at its approval commit, or the configured solo trailer.",
                    path=_relative(review_state_path, self.workspace),
                    artifact_id=artifact_id,
                    field="implementation_refs",
                    hint="Refresh the cache from verified provider review or an explicit solo commit trailer before handoff.",
                )
            elif verification_mode == "solo_commit":
                self.report.warning(
                    "SOLO_REVIEW_SELF_ATTESTED",
                    "solo_commit verification is self-attestation, not independent identity proof.",
                    path=_relative(review_state_path, self.workspace),
                    artifact_id=artifact_id,
                )
            return approved_version
        self.report.error(
            "IMPLEMENTATION_REVIEW_STATE_UNAVAILABLE",
            f"Review state has no approved_version for PRD '{artifact_id}'.",
            path=_relative(review_state_path, self.workspace),
            artifact_id=artifact_id,
            field="implementation_refs",
            hint="Record this PRD's approved_version before implementation handoff.",
        )
        return None

    def _validate_implementation_refs(self, document: MarkdownDocument) -> None:
        metadata = document.metadata
        refs = metadata.get("implementation_refs")
        if refs is None:
            return
        path = _relative(document.path, self.workspace)
        artifact_id = metadata.get("id")
        if not isinstance(refs, list):
            self.report.error(
                "IMPLEMENTATION_REFS_MALFORMED",
                "implementation_refs must be an array of external plan references.",
                path=path,
                artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                field="implementation_refs",
                hint="Use a list containing repository, path, based_on_prd_id, and based_on_prd_version.",
            )
            return
        if not refs:
            return
        current_version = self._current_prd_version(metadata, path=path)
        for index, ref in enumerate(refs):
            field_prefix = f"implementation_refs.{index}"
            if not isinstance(ref, Mapping):
                self.report.error(
                    "IMPLEMENTATION_REF_MALFORMED",
                    "Implementation reference must be an object.",
                    path=path,
                    artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                    field=field_prefix,
                    hint="Provide repository, path, based_on_prd_id, and based_on_prd_version.",
                )
                continue
            for required in ("repository", "path", "based_on_prd_id", "based_on_prd_version"):
                if not _has(ref, required):
                    self.report.error(
                        "IMPLEMENTATION_REF_INCOMPLETE",
                        f"Implementation reference is missing '{required}'.",
                        path=path,
                        artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                        field=f"{field_prefix}.{required}",
                        hint="External plan references require repository, path, source PRD ID, and source PRD version.",
                    )
            if ref.get("based_on_prd_id") != artifact_id:
                self.report.error(
                    "IMPLEMENTATION_REF_PRD_MISMATCH",
                    f"Implementation plan is based on '{ref.get('based_on_prd_id')}', not its owning PRD '{artifact_id}'.",
                    path=path,
                    artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                    field=f"{field_prefix}.based_on_prd_id",
                    hint="Point the reference at the owning PRD stable ID.",
                )
            if current_version is not None and ref.get("based_on_prd_version") != current_version:
                self.report.error(
                    "IMPLEMENTATION_REF_STALE",
                    f"Implementation plan uses PRD version '{ref.get('based_on_prd_version')}', current approved version is '{current_version}'.",
                    path=path,
                    artifact_id=artifact_id if isinstance(artifact_id, str) else None,
                    field=f"{field_prefix}.based_on_prd_version",
                    hint="Ask engineering to review the plan against the current approved PRD version; do not rewrite the external plan automatically.",
                )

    def _canonical_adapter_hash(self, root: Path) -> tuple[str, int]:
        digest = hashlib.sha256()
        count = 0
        paths = sorted(
            candidate
            for directory in (root / "skills", root / "integrations")
            if directory.is_dir()
            for candidate in directory.rglob("*")
            if candidate.is_file()
        )
        for path in paths:
            relative = path.relative_to(root).as_posix().encode("utf-8")
            digest.update(relative)
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
            count += 1
        return digest.hexdigest(), count

    def _validate_adapters(self) -> None:
        before = len(self.report.errors)
        adapters_dir = self._asset_dir("adapters")
        source_root = adapters_dir.parent if adapters_dir else self.workspace
        if adapters_dir is None:
            self.report.error(
                "ADAPTERS_MISSING",
                "No generated adapters directory is available.",
                hint="Generate adapters from canonical skills/ and integrations/ before installation.",
            )
            self.report.check("generated-adapters", before, "no adapters found")
            return
        unsafe_source = False
        for directory in (source_root / "skills", source_root / "integrations", adapters_dir):
            if not directory.exists() and not directory.is_symlink():
                continue
            for candidate in (directory, *directory.rglob("*")):
                if candidate.is_symlink() or not self._safe_contained_path(candidate, source_root):
                    self._report_unsafe_path(candidate, "adapter/canonical asset")
                    unsafe_source = True
        if unsafe_source:
            self.report.check("generated-adapters", before, "rejected unsafe adapter/canonical paths")
            return
        try:
            canonical_hash, source_count = self._canonical_adapter_hash(source_root)
        except (OSError, UnicodeError) as exc:
            self.report.error(
                "ADAPTER_CANONICAL_SOURCE_UNREADABLE",
                f"Cannot read canonical adapter source: {_bounded_message(str(exc))}",
                path=_relative(source_root, self.workspace),
                hint="Restore readable canonical skills and integration descriptors.",
            )
            self.report.check("generated-adapters", before, "canonical source unreadable")
            return
        manifests = sorted(adapters_dir.glob("*/manifest.yaml")) + sorted(adapters_dir.glob("*/manifest.yml"))
        if not manifests:
            self.report.error(
                "ADAPTER_MANIFESTS_MISSING",
                "No adapters/<client>/manifest.yaml files were found.",
                path=_relative(adapters_dir, self.workspace),
                hint="Regenerate client adapters from the canonical source.",
            )
        for manifest_path in manifests:
            try:
                manifest = load_yaml_strict(manifest_path.read_text(encoding="utf-8")) or {}
            except (OSError, UnicodeError, ValueError, yaml.YAMLError):
                self.report.error(
                    "ADAPTER_MANIFEST_INVALID",
                    "Cannot parse adapter manifest as strict UTF-8 YAML.",
                    path=_relative(manifest_path, self.workspace),
                    hint="Regenerate the adapter manifest; do not edit generated metadata by hand.",
                )
                continue
            if not isinstance(manifest, Mapping):
                self.report.error(
                    "ADAPTER_MANIFEST_INVALID",
                    "Adapter manifest root must be an object.",
                    path=_relative(manifest_path, self.workspace),
                    hint="Regenerate the adapter manifest from canonical source.",
                )
                continue
            canonical = manifest.get("canonical_source")
            expected = canonical.get("content_hash") if isinstance(canonical, Mapping) else None
            algorithm = canonical.get("hash_algorithm") if isinstance(canonical, Mapping) else None
            if manifest.get("generated") is not True or algorithm != "sha256" or not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
                self.report.error(
                    "ADAPTER_HASH_METADATA_INVALID",
                    "Adapter manifest must declare generated: true and canonical_source hash_algorithm/content_hash.",
                    path=_relative(manifest_path, self.workspace),
                    hint="Regenerate this adapter from canonical skills/ and integrations/.",
                )
                continue
            if source_count == 0:
                self.report.error(
                    "ADAPTER_CANONICAL_SOURCE_MISSING",
                    "Cannot verify adapter hash because canonical skills/ and integrations/ contain no files.",
                    path=_relative(manifest_path, self.workspace),
                    hint="Install the canonical source alongside generated adapters.",
                )
            elif expected.lower() != canonical_hash:
                self.report.error(
                    "ADAPTER_HASH_STALE",
                    f"Adapter records canonical hash {expected.lower()}, observed {canonical_hash}.",
                    path=_relative(manifest_path, self.workspace),
                    hint="Regenerate every client adapter after canonical skills or integrations change.",
                )
            marker_path = manifest_path.parent / "ADAPTER.md"
            if not marker_path.is_file():
                self.report.error(
                    "ADAPTER_MARKER_INVALID",
                    "Generated adapter must include ADAPTER.md with exactly one canonical_sha256 marker.",
                    path=_relative(marker_path, self.workspace),
                    hint="Regenerate ADAPTER.md together with its manifest.",
                )
                continue
            try:
                marker = marker_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                self.report.error(
                    "ADAPTER_MARKER_INVALID",
                    f"Cannot read ADAPTER.md: {_bounded_message(str(exc))}",
                    path=_relative(marker_path, self.workspace),
                    hint="Regenerate a UTF-8 ADAPTER.md together with its manifest.",
                )
                continue
            matches = re.findall(r"canonical_sha256=([0-9a-fA-F]{64})(?![0-9a-fA-F])", marker)
            if len(matches) != 1:
                self.report.error(
                    "ADAPTER_MARKER_INVALID",
                    "ADAPTER.md must contain exactly one canonical_sha256=HASH marker.",
                    path=_relative(marker_path, self.workspace),
                    hint="Regenerate ADAPTER.md together with its manifest.",
                )
            elif matches[0].lower() != expected.lower() or matches[0].lower() != canonical_hash:
                self.report.error(
                    "ADAPTER_MARKER_STALE",
                    "ADAPTER.md canonical_sha256 does not match its manifest and canonical source content.",
                    path=_relative(marker_path, self.workspace),
                    hint="Regenerate ADAPTER.md together with its manifest.",
                )
        self.report.check("generated-adapters", before, f"checked {len(manifests)} adapter manifest(s) against {source_count} canonical file(s)")

    def _smoke_checks(self) -> None:
        before = len(self.report.errors)
        self._validate_release_provenance()
        self.report.check("release-provenance", before, "verified installed/source manifest hashes")

        before = len(self.report.errors)
        try:
            git_root = self._git("rev-parse", "--show-toplevel")
        except (OSError, UnicodeError, subprocess.SubprocessError) as exc:
            git_root = None
            self.report.error(
                "GIT_REPOSITORY_UNAVAILABLE",
                f"Cannot access workspace Git repository: {_bounded_message(str(exc))}",
                hint="Run smoke-test inside an initialized, readable Git worktree.",
            )
        if git_root is not None and git_root.returncode != 0:
            self.report.error(
                "GIT_REPOSITORY_UNAVAILABLE",
                "Workspace is not inside an accessible Git repository.",
                hint="Run smoke-test inside an initialized, readable Git worktree.",
            )
        self.report.check("git-access", before, "checked local Git repository access")

        before = len(self.report.errors)
        integrations_dir = self._asset_dir("integrations")
        connectors = self.config.get("connectors")
        connector_count = 0
        if isinstance(connectors, Mapping):
            for capability, provider in sorted(connectors.items(), key=lambda item: str(item[0])):
                connector_count += 1
                descriptor = integrations_dir / "providers" / f"{provider}.yaml" if integrations_dir else None
                if (
                    descriptor is None
                    or not descriptor.is_file()
                    or not self._safe_contained_path(descriptor, integrations_dir)
                ):
                    self.report.error(
                        "CONNECTOR_DESCRIPTOR_MISSING",
                        f"Connector '{capability}' names provider '{provider}' without an installed descriptor.",
                        path=_relative(descriptor, self.workspace) if descriptor else "integrations/providers",
                        field=f"connectors.{capability}",
                        hint=f"Install integrations/providers/{provider}.yaml or correct the configured provider name.",
                    )
        self.report.warning(
            "LIVE_MCP_CHECKS_AGENT_OWNED",
            "Static smoke-test verifies connector descriptors only; live MCP capability and authorization checks remain agent-owned.",
            hint="Have the executing agent verify required live connector capabilities before using external data.",
        )
        self.report.check("connector-descriptors", before, f"checked {connector_count} named connector descriptor(s)")

        before = len(self.report.errors)
        self._validate_active_wrapper_projection()
        self.report.check("active-wrapper-projection", before, "checked selected client wrapper destinations")

        before = len(self.report.errors)
        skills_dir = self._asset_dir("skills")
        skill_files = [
            path for path in sorted(skills_dir.rglob("SKILL.md"))
            if self._safe_contained_path(path, skills_dir)
        ] if skills_dir else []
        if not skill_files:
            self.report.error(
                "SKILLS_NOT_DISCOVERABLE",
                "No canonical skills/*/SKILL.md files are discoverable.",
                hint="Install canonical skills before running smoke-test.",
            )
        self.report.check("skill-discovery", before, f"discovered {len(skill_files)} canonical skill(s)")

        before = len(self.report.errors)
        sensitive_files: list[Path] = []
        pii_files: list[Path] = []
        scan_roots = [
            path for path in (
                self.workspace / ".product-os",
                self.workspace / "adapters",
                self.workspace / "integrations",
                self.workspace / "product",
            ) if path.is_dir()
        ]
        for client_root in (self.workspace / ".agents" / "skills", self.workspace / ".claude" / "skills"):
            if client_root.is_dir():
                scan_roots.extend(path for path in client_root.glob("product-os-*") if path.is_dir() or path.is_symlink())
        for root in scan_roots:
            if not self._safe_contained_path(root, self.workspace):
                self._report_unsafe_path(root, "secret/PII scan root")
                continue
            for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file() or candidate.is_symlink()):
                if not self._safe_contained_path(path, self.workspace):
                    self._report_unsafe_path(path, "proposed content")
                    continue
                try:
                    if path.stat().st_size > 1_000_000:
                        continue
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    continue
                if any(pattern.search(text) for _, pattern in CREDENTIAL_PATTERNS):
                    sensitive_files.append(path)
                if any(pattern.search(text) for pattern in PII_PATTERNS):
                    pii_files.append(path)
        try:
            staged = self._git("diff", "--cached", "--no-ext-diff", "--unified=0", "--", ".")
        except (OSError, UnicodeError, subprocess.SubprocessError):
            staged = None
        staged_text = staged.stdout if staged is not None and staged.returncode == 0 else ""
        staged_secret = any(pattern.search(staged_text) for _, pattern in CREDENTIAL_PATTERNS)
        staged_pii = any(pattern.search(staged_text) for pattern in PII_PATTERNS)
        for path in sensitive_files:
            self.report.error(
                "CREDENTIAL_LIKE_CONTENT",
                "Credential-like content detected in installed configuration or adapter metadata.",
                path=_relative(path, self.workspace),
                hint="Remove and rotate the secret; adapters must never contain credentials.",
            )
        if staged_secret:
            self.report.error(
                "CREDENTIAL_LIKE_CONTENT",
                "Credential-like content detected in the staged Git diff.",
                path="<staged-diff>",
                hint="Remove and rotate the secret before committing.",
            )
        for path in pii_files:
            self.report.warning(
                "PII_LIKE_CONTENT",
                "Common PII-like content detected by a heuristic scan; no value is included in this report.",
                path=_relative(path, self.workspace),
                hint="Confirm necessity, consent, minimization, and reference-only storage before proceeding.",
            )
        if staged_pii:
            self.report.warning(
                "PII_LIKE_CONTENT",
                "Common PII-like content detected heuristically in the staged Git diff.",
                path="<staged-diff>",
            )
        self.report.warning(
            "HEURISTIC_CONTENT_SCAN_LIMITED",
            "Credential and PII scans are heuristic safeguards and do not guarantee detection.",
        )
        self.report.check(
            "credential-scan",
            before,
            f"heuristically scanned proposed/staged content; flagged {len(sensitive_files) + int(staged_secret)} credential location(s)",
        )

    def _validate_active_wrapper_projection(self) -> None:
        adapter_config = self.config.get("adapter") if isinstance(self.config.get("adapter"), Mapping) else {}
        selected = self.config.get("selected_client") or self.config.get("client") or adapter_config.get("client")
        if not isinstance(selected, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", selected):
            self.report.error(
                "ACTIVE_CLIENT_NOT_CONFIGURED",
                "Smoke-test requires a safe selected client adapter name in config.",
                field="selected_client",
                hint="Set selected_client to an installed adapters/<client>/ manifest name.",
            )
            return
        adapters_dir = self._asset_dir("adapters")
        manifest_path = adapters_dir / selected / "manifest.yaml" if adapters_dir else None
        if manifest_path is None or not manifest_path.is_file() or not self._safe_contained_path(manifest_path, adapters_dir):
            self.report.error(
                "ACTIVE_ADAPTER_MANIFEST_MISSING",
                "Selected client adapter manifest is missing or unsafe.",
                path=_relative(manifest_path, self.workspace) if manifest_path else "adapters",
                hint="Install the selected generated adapter under the canonical adapters directory.",
            )
            return
        try:
            manifest = load_yaml_strict(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError, yaml.YAMLError):
            self.report.error(
                "ACTIVE_ADAPTER_MANIFEST_INVALID",
                "Selected client adapter manifest is not readable strict UTF-8 YAML.",
                path=_relative(manifest_path, self.workspace),
            )
            return
        projections = manifest.get("projections") if isinstance(manifest, Mapping) else None
        if not isinstance(manifest, Mapping) or manifest.get("client") != selected or not isinstance(projections, list) or not projections:
            self.report.error(
                "ACTIVE_ADAPTER_MANIFEST_INVALID",
                "Selected adapter manifest must match the configured client and declare projections.",
                path=_relative(manifest_path, self.workspace),
            )
            return
        source_root = adapters_dir.parent
        expected_destinations: set[Path] = set()
        discovery_roots: set[Path] = set()
        for index, projection in enumerate(projections):
            if not isinstance(projection, Mapping):
                self.report.error("ACTIVE_ADAPTER_PROJECTION_INVALID", f"Projection {index} must be an object.")
                continue
            wrapper_value = projection.get("wrapper_source")
            destination_value = projection.get("destination")
            if not isinstance(wrapper_value, str) or not isinstance(destination_value, str):
                self.report.error("ACTIVE_ADAPTER_PROJECTION_INVALID", f"Projection {index} lacks wrapper_source/destination.")
                continue
            wrapper = source_root / wrapper_value
            destination = self.workspace / destination_value
            expected_destinations.add(destination)
            discovery_roots.add(
                destination.parent.parent
                if destination.parent.name.startswith("product-os-")
                else destination.parent
            )
            if not wrapper.is_file() or not destination.is_file():
                if wrapper.is_symlink():
                    self._report_unsafe_path(wrapper, "adapter wrapper source")
                if destination.is_symlink():
                    self._report_unsafe_path(destination, "installed adapter wrapper")
                if not wrapper.is_symlink() and not destination.is_symlink():
                    self.report.error(
                        "ACTIVE_WRAPPER_MISSING",
                        "A declared active wrapper source or installed destination is missing.",
                        path=_relative(destination, self.workspace),
                        hint="Install every projection at the exact destination declared by the adapter manifest.",
                    )
                continue
            if not self._safe_contained_path(wrapper, source_root):
                self._report_unsafe_path(wrapper, "adapter wrapper source")
                continue
            if not self._safe_contained_path(destination, self.workspace):
                self._report_unsafe_path(destination, "installed adapter wrapper")
                continue
            try:
                source_bytes = wrapper.read_bytes()
                destination_bytes = destination.read_bytes()
            except OSError:
                self.report.error("ACTIVE_WRAPPER_UNREADABLE", "A declared active wrapper cannot be read safely.")
                continue
            if source_bytes != destination_bytes:
                self.report.error(
                    "ACTIVE_WRAPPER_MISMATCH",
                    "Installed wrapper bytes/hash do not match the generated adapter projection.",
                    path=_relative(destination, self.workspace),
                    hint="Replace it with the exact generated wrapper_source bytes.",
                )
        for discovery_root in discovery_roots:
            if not discovery_root.is_dir() or not self._safe_contained_path(discovery_root, self.workspace):
                continue
            for candidate in discovery_root.glob("product-os-*"):
                if candidate.is_symlink() or not self._safe_contained_path(candidate, self.workspace):
                    self._report_unsafe_path(candidate, "installed product-os wrapper namespace")
                    continue
                declared = any(destination == candidate or candidate in destination.parents for destination in expected_destinations)
                if not declared:
                    self.report.error(
                        "ACTIVE_WRAPPER_EXTRA",
                        "Undeclared entry exists in the active product-os wrapper namespace.",
                        path=_relative(candidate, self.workspace),
                        hint="Remove stale generated wrappers not declared by the selected adapter manifest.",
                    )

    def _validate_release_provenance(self) -> None:
        installed_path = self.workspace / ".product-os" / "installed-manifest.json"
        release_copy = self.workspace / ".product-os" / "release-manifest.json"
        if installed_path.is_file() or installed_path.is_symlink():
            self._validate_installed_provenance(installed_path, release_copy)
            return
        if release_copy.is_file() or release_copy.is_symlink():
            self.report.error(
                "INSTALLED_MANIFEST_MISSING",
                "Installed workspace has release provenance but no installed-manifest.json.",
                path=".product-os/installed-manifest.json",
                hint="Re-run the trusted installer; do not infer a partial install from the full release file list.",
            )
            return
        distribution_root = self._distribution_root()
        candidates = (
            (self.workspace / "manifest.json", self.workspace),
            (distribution_root / "manifest.json", distribution_root) if distribution_root else None,
        )
        selected = next(
            ((manifest_path, root) for item in candidates if item is not None for manifest_path, root in (item,) if manifest_path.is_file()),
            None,
        )
        if selected is None:
            self.report.error(
                "PROVENANCE_MANIFEST_MISSING",
                "No local release/install manifest.json is available.",
                hint="Install a complete immutable release including manifest.json before smoke-test.",
            )
            return
        manifest_path, root = selected
        if not self._safe_contained_path(manifest_path, root):
            self._report_unsafe_path(manifest_path, "release provenance manifest")
            return
        try:
            if manifest_path.stat().st_size > 5_000_000:
                raise ValueError("manifest exceeds 5000000 bytes")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(manifest, Mapping):
                raise ValueError("manifest root must be an object")
            entries = manifest.get("files")
            if (
                manifest.get("manifest_version") != 1
                or manifest.get("hash_algorithm") != "sha256"
                or not isinstance(manifest.get("tree_digest"), str)
                or not SHA256_RE.fullmatch(manifest["tree_digest"])
                or not isinstance(entries, list)
            ):
                raise ValueError("manifest metadata/files do not match manifest version 1")
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            self.report.error(
                "PROVENANCE_MANIFEST_INVALID",
                f"Cannot validate release manifest: {_bounded_message(str(exc))}",
                path=_relative(manifest_path, self.workspace),
                hint="Reinstall or regenerate the canonical manifest from trusted release contents.",
            )
            return
        digest = hashlib.sha256()
        seen: set[str] = set()
        for index, entry in enumerate(entries):
            if not isinstance(entry, Mapping):
                self.report.error(
                    "PROVENANCE_MANIFEST_INVALID",
                    f"Manifest file entry {index} must be an object.",
                    path=_relative(manifest_path, self.workspace),
                )
                return
            relative = entry.get("path")
            expected_hash = entry.get("sha256")
            expected_size = entry.get("size")
            if (
                not isinstance(relative, str)
                or not relative
                or relative in seen
                or Path(relative).is_absolute()
                or ".." in Path(relative).parts
                or not isinstance(expected_hash, str)
                or not SHA256_RE.fullmatch(expected_hash)
                or not isinstance(expected_size, int)
                or expected_size < 0
            ):
                self.report.error(
                    "PROVENANCE_MANIFEST_INVALID",
                    f"Manifest file entry {index} has an unsafe path or invalid hash/size.",
                    path=_relative(manifest_path, self.workspace),
                )
                return
            seen.add(relative)
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(expected_hash.lower().encode("ascii"))
            digest.update(b"\0")
            target = root / relative
            if not target.exists() and not target.is_symlink():
                self.report.error(
                    "PROVENANCE_FILE_MISSING",
                    f"Manifest file '{relative}' is unavailable.",
                    path=_relative(target, self.workspace),
                    hint="Restore the complete release/install contents.",
                )
                continue
            if not self._safe_contained_path(target, root):
                self._report_unsafe_path(target, "release provenance file")
                continue
            try:
                observed_size = target.stat().st_size
                observed_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            except OSError as exc:
                self.report.error(
                    "PROVENANCE_FILE_MISSING",
                    f"Manifest file '{relative}' is unavailable: {_bounded_message(str(exc))}",
                    path=_relative(target, self.workspace),
                    hint="Restore the complete release/install contents.",
                )
                continue
            if observed_size != expected_size or observed_hash != expected_hash.lower():
                self.report.error(
                    "PROVENANCE_FILE_MISMATCH",
                    f"Manifest hash/size mismatch for '{relative}'.",
                    path=_relative(target, self.workspace),
                    hint="Replace modified files with trusted release contents.",
                )
        if digest.hexdigest() != manifest["tree_digest"].lower():
            self.report.error(
                "PROVENANCE_TREE_DIGEST_MISMATCH",
                "Manifest tree_digest does not match its ordered file entries.",
                path=_relative(manifest_path, self.workspace),
                hint="Reinstall or regenerate the canonical manifest.",
            )

    def _read_json_object(self, path: Path, *, code: str, label: str) -> Mapping[str, Any] | None:
        if not path.is_file() and not path.is_symlink():
            self.report.error(
                code,
                f"{label.capitalize()} is missing.",
                path=_relative(path, self.workspace),
            )
            return None
        if not self._safe_contained_path(path, self.workspace):
            self._report_unsafe_path(path, label)
            return None
        try:
            if path.stat().st_size > 5_000_000:
                raise ValueError("oversized")
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, Mapping):
                raise ValueError("not an object")
            return value
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
            self.report.error(
                code,
                f"{label.capitalize()} is not a valid bounded UTF-8 JSON object.",
                path=_relative(path, self.workspace),
            )
            return None

    def _manifest_entries(
        self,
        manifest: Mapping[str, Any],
        *,
        manifest_path: Path,
        verify_files: bool,
    ) -> dict[str, tuple[str, int]] | None:
        entries = manifest.get("files")
        tree_digest = manifest.get("tree_digest")
        if not isinstance(entries, list) or not isinstance(tree_digest, str) or not SHA256_RE.fullmatch(tree_digest):
            self.report.error(
                "PROVENANCE_MANIFEST_INVALID",
                "Manifest files/tree_digest metadata is invalid.",
                path=_relative(manifest_path, self.workspace),
            )
            return None
        paths = [entry.get("path") for entry in entries if isinstance(entry, Mapping)]
        if len(paths) != len(entries) or paths != sorted(paths):
            self.report.error(
                "PROVENANCE_MANIFEST_INVALID",
                "Manifest file entries must be objects sorted by path.",
                path=_relative(manifest_path, self.workspace),
            )
            return None
        result: dict[str, tuple[str, int]] = {}
        digest = hashlib.sha256()
        for index, entry in enumerate(entries):
            relative = entry.get("path")
            expected_hash = entry.get("sha256")
            expected_size = entry.get("size")
            if (
                not isinstance(relative, str)
                or not relative
                or relative in result
                or Path(relative).is_absolute()
                or ".." in Path(relative).parts
                or not isinstance(expected_hash, str)
                or not SHA256_RE.fullmatch(expected_hash)
                or not isinstance(expected_size, int)
                or expected_size < 0
            ):
                self.report.error(
                    "PROVENANCE_MANIFEST_INVALID",
                    f"Manifest file entry {index} has an unsafe path or invalid hash/size.",
                    path=_relative(manifest_path, self.workspace),
                )
                return None
            result[relative] = (expected_hash.lower(), expected_size)
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(expected_hash.lower().encode("ascii"))
            digest.update(b"\0")
            if verify_files:
                target = self.workspace / relative
                if not target.exists() and not target.is_symlink():
                    self.report.error(
                        "PROVENANCE_FILE_MISSING",
                        "A scoped installed file is unavailable.",
                        path=_relative(target, self.workspace),
                    )
                    continue
                if not self._safe_contained_path(target, self.workspace):
                    self._report_unsafe_path(target, "installed manifest file")
                    continue
                try:
                    observed = target.read_bytes()
                except OSError:
                    self.report.error(
                        "PROVENANCE_FILE_MISSING",
                        "A scoped installed file is unavailable.",
                        path=_relative(target, self.workspace),
                    )
                    continue
                if len(observed) != expected_size or hashlib.sha256(observed).hexdigest() != expected_hash.lower():
                    self.report.error(
                        "PROVENANCE_FILE_MISMATCH",
                        "A scoped installed file does not match its recorded hash/size.",
                        path=_relative(target, self.workspace),
                    )
        if digest.hexdigest() != tree_digest.lower():
            self.report.error(
                "PROVENANCE_TREE_DIGEST_MISMATCH",
                "Manifest tree_digest does not match its ordered file entries.",
                path=_relative(manifest_path, self.workspace),
            )
        return result

    def _validate_installed_provenance(self, installed_path: Path, release_path: Path) -> None:
        installed = self._read_json_object(
            installed_path, code="INSTALLED_MANIFEST_INVALID", label="installed manifest"
        )
        release = self._read_json_object(
            release_path, code="RELEASE_MANIFEST_INVALID", label="release manifest copy"
        )
        if installed is None or release is None:
            return
        client = installed.get("client")
        if (
            installed.get("manifest_version") != 1
            or installed.get("manifest_kind") != "installed_workspace"
            or installed.get("hash_algorithm") != "sha256"
            or client not in {"codex", "claude-code", "openclaw"}
        ):
            self.report.error(
                "INSTALLED_MANIFEST_INVALID",
                "Installed manifest identity, hash algorithm, or client is invalid.",
                path=_relative(installed_path, self.workspace),
            )
            return
        configured_client = self.config.get("selected_client") or self.config.get("client")
        if isinstance(configured_client, str) and configured_client != client:
            self.report.error(
                "INSTALLED_MANIFEST_CLIENT_MISMATCH",
                "Installed manifest client does not match workspace configuration.",
                path=_relative(installed_path, self.workspace),
                field="client",
            )
        installed_entries = self._manifest_entries(
            installed, manifest_path=installed_path, verify_files=True
        )
        release_entries = self._manifest_entries(
            release, manifest_path=release_path, verify_files=False
        )
        if installed_entries is None or release_entries is None:
            return
        required_scoped = {
            ".product-os/release-manifest.json",
            ".product-os/install-plan.json",
            ".product-os/config.yaml",
        }
        missing_scoped = required_scoped - installed_entries.keys()
        if missing_scoped:
            self.report.error(
                "INSTALLED_MANIFEST_INCOMPLETE",
                "Installed manifest omits required provenance/config files.",
                path=_relative(installed_path, self.workspace),
            )
        if ".product-os/installed-manifest.json" in installed_entries:
            self.report.error(
                "INSTALLED_MANIFEST_INVALID",
                "Installed manifest must exclude itself from scoped files.",
                path=_relative(installed_path, self.workspace),
            )
        parent = installed.get("parent_release")
        parent_fields = ("product", "release", "canonical_origin", "publisher", "tree_digest")
        if not isinstance(parent, Mapping) or any(parent.get(key) != release.get(key) for key in parent_fields):
            self.report.error(
                "PARENT_RELEASE_PROVENANCE_MISMATCH",
                "Installed manifest parent_release does not match the verbatim release manifest.",
                path=_relative(installed_path, self.workspace),
            )
        if release.get("manifest_version") != 1 or release.get("hash_algorithm") != "sha256":
            self.report.error(
                "RELEASE_MANIFEST_INVALID",
                "Release manifest copy has unsupported identity/hash metadata.",
                path=_relative(release_path, self.workspace),
            )
        plan_path = self.workspace / ".product-os" / "install-plan.json"
        plan = self._read_json_object(plan_path, code="INSTALL_PLAN_INVALID", label="install plan")
        if plan is None:
            return
        plan_files = plan.get("files")
        if (
            plan.get("plan_version") != 1
            or plan.get("client") != client
            or plan.get("release_tree_digest") != release.get("tree_digest")
            or not isinstance(plan_files, list)
        ):
            self.report.error(
                "INSTALL_PLAN_INVALID",
                "Install plan identity/client/release provenance is invalid.",
                path=_relative(plan_path, self.workspace),
            )
            return
        canonical_payload = {
            "plan_version": 1,
            "client": client,
            "release_tree_digest": plan.get("release_tree_digest"),
            "config_sha256": plan.get("config_sha256"),
            "files": plan_files,
        }
        computed_plan_hash = hashlib.sha256(
            json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if (
            plan.get("plan_hash") != computed_plan_hash
            or installed.get("install_plan_sha256") != computed_plan_hash
        ):
            self.report.error(
                "INSTALL_PLAN_HASH_MISMATCH",
                "Install plan canonical hash does not match persisted provenance.",
                path=_relative(plan_path, self.workspace),
            )
        destinations: dict[str, tuple[str, int]] = {}
        ordered_destinations: list[str] = []
        for index, item in enumerate(plan_files):
            if not isinstance(item, Mapping):
                self.report.error("INSTALL_PLAN_INVALID", f"Install plan file entry {index} is invalid.")
                return
            source = item.get("source")
            destination = item.get("destination")
            sha256 = item.get("sha256")
            size = item.get("size")
            source_safe = source == "@config" or (
                isinstance(source, str)
                and source
                and not Path(source).is_absolute()
                and ".." not in Path(source).parts
            )
            if (
                not source_safe
                or not isinstance(destination, str)
                or not destination
                or Path(destination).is_absolute()
                or ".." in Path(destination).parts
                or item.get("action") != "create"
                or not isinstance(sha256, str)
                or not SHA256_RE.fullmatch(sha256)
                or not isinstance(size, int)
                or size < 0
                or destination in destinations
            ):
                self.report.error("INSTALL_PLAN_INVALID", f"Install plan file entry {index} is invalid.")
                return
            ordered_destinations.append(destination)
            destinations[destination] = (sha256.lower(), size)
        if ordered_destinations != sorted(ordered_destinations):
            self.report.error(
                "INSTALL_PLAN_INVALID",
                "Install plan files must be sorted by destination.",
                path=_relative(plan_path, self.workspace),
            )
        scoped_without_plan = {
            path: value for path, value in installed_entries.items()
            if path != ".product-os/install-plan.json"
        }
        if destinations != scoped_without_plan:
            self.report.error(
                "INSTALL_PLAN_SCOPE_MISMATCH",
                "Planned destination/hash/size pairs do not match scoped installed provenance.",
                path=_relative(plan_path, self.workspace),
            )
        config_entry = installed_entries.get(".product-os/config.yaml")
        if config_entry is None or plan.get("config_sha256") != config_entry[0]:
            self.report.error(
                "INSTALL_PLAN_CONFIG_MISMATCH",
                "Install plan config hash does not match installed config provenance.",
                path=_relative(plan_path, self.workspace),
            )


def validate_workspace(
    workspace: str | Path,
    command: str = "validate",
    *,
    base_ref: str | None = None,
) -> ValidationReport:
    if command not in {"validate", "smoke-test", "adapter-check"}:
        report = ValidationReport(command=command, workspace=Path(workspace).resolve(), configuration_error=True)
        report.error("COMMAND_UNKNOWN", f"Unknown command: {command!r}.")
        return report
    return WorkspaceValidator(Path(workspace), command=command, base_ref=base_ref).run()
