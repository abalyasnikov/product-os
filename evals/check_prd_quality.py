#!/usr/bin/env python3
"""Run deterministic PRD-quality contract checks over the golden case set.

This is intentionally not an LLM evaluator. It verifies observable repository
invariants only; semantic product judgment remains outside this executable layer.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from product_os.frontmatter import (  # noqa: E402
    FrontmatterError,
    MarkdownDocument,
    parse_markdown,
    structured_blocks,
)

RUBRIC_PATH = Path(__file__).with_name("prd-quality-rubric.yaml")
CASES_ROOT = Path(__file__).with_name("cases")
METRIC_CLAIM = re.compile(
    r"(?<![A-Za-z0-9_])(?:[$€£]\s?\d[\d,.]*[kKmMbB]?|\d+(?:\.\d+)?\s?%|"
    r"\d+(?:\.\d+)?\s+(?:users?|accounts?|interviews?|calls?|requests?|tickets?|"
    r"sessions?|days?|weeks?|months?|years?))",
    re.IGNORECASE,
)
SIGNAL_ID = re.compile(r"\bsignal_[A-Za-z0-9_-]+\b")
H2 = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
H3 = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Violation:
    code: str
    case: str
    path: str
    message: str


def _load_yaml(path: Path) -> Mapping[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"expected a YAML object: {path}")
    return value


def _headings(body: str, pattern: re.Pattern[str]) -> set[str]:
    return {match.group(1).strip().casefold() for match in pattern.finditer(body)}


def _section(body: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        body,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    return match.group(1) if match else ""


def _add(
    violations: list[Violation], code: str, case: str, path: Path, message: str
) -> None:
    violations.append(Violation(code, case, path.as_posix(), message))


def _check_document(
    case_name: str,
    case_root: Path,
    document: MarkdownDocument,
    expected: Mapping[str, Any],
    case: Mapping[str, Any],
    rubric: Mapping[str, Any],
) -> list[Violation]:
    violations: list[Violation] = []
    path = document.path.relative_to(case_root)
    metadata = document.metadata
    artifact_type = metadata.get("type")
    if artifact_type != expected.get("type"):
        _add(violations, "TYPE_MISMATCH", case_name, path, "artifact type differs from case expectation")
        return violations

    contract = rubric["deterministic_contract"]
    required = contract["required_sections"].get(artifact_type, [])
    headings = _headings(document.body, H2)
    for heading in required:
        if str(heading).casefold() not in headings:
            _add(violations, "SECTION_MISSING", case_name, path, f"missing ## {heading}")

    required_subsections = contract.get("required_subsections", {}).get(artifact_type, {})
    for parent, children in required_subsections.items():
        subsection_headings = _headings(_section(document.body, str(parent)), H3)
        for child in children:
            if str(child).casefold() not in subsection_headings:
                _add(
                    violations,
                    "SUBSECTION_MISSING",
                    case_name,
                    path,
                    f"missing ### {child} under ## {parent}",
                )

    if artifact_type == "prd" and not re.search(
        r"(?im)^\*\*Why now / business reality:\*\*\s+\S", _section(document.body, "Problem")
    ):
        _add(
            violations,
            "WHY_NOW_MISSING",
            case_name,
            path,
            "Problem must contain a compact **Why now / business reality:** statement",
        )

    expected_evidence = set(expected.get("evidence_ids", []))
    known_evidence = {
        str(item["id"])
        for item in case.get("source_facts", [])
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    evidence_section = _section(
        document.body,
        "Evidence" if artifact_type == "prd" else "Evidence and confidence",
    )
    relationships = metadata.get("relationships")
    related_signals = set(
        relationships.get("signals", []) if isinstance(relationships, Mapping) else []
    )
    for evidence_id in expected_evidence:
        if evidence_id not in related_signals or evidence_id not in evidence_section:
            _add(
                violations,
                "EVIDENCE_NOT_TRACEABLE",
                case_name,
                path,
                f"{evidence_id} must appear in relationships.signals and the evidence section",
            )
    observed_ids = set(SIGNAL_ID.findall(document.body)) | related_signals
    for evidence_id in sorted(observed_ids - known_evidence):
        _add(
            violations,
            "UNKNOWN_EVIDENCE_REFERENCE",
            case_name,
            path,
            f"{evidence_id} is not present in case source facts",
        )

    allowed_numeric = [str(value) for value in case.get("allowed_numeric_claims", [])]
    uncertainty = [str(value).casefold() for value in contract.get("uncertainty_markers", [])]
    for line_number, line in enumerate(document.body.splitlines(), start=1):
        for match in METRIC_CLAIM.finditer(line):
            if any(value in line for value in allowed_numeric):
                continue
            if any(marker in line.casefold() for marker in uncertainty):
                continue
            _add(
                violations,
                "UNSUPPORTED_NUMERIC_CLAIM",
                case_name,
                path,
                f"line {line_number} contains unsupported numeric claim {match.group(0)!r}",
            )

    for expression in contract.get("forbidden_implementation_patterns", []):
        if re.search(str(expression), document.body, re.MULTILINE):
            _add(
                violations,
                "IMPLEMENTATION_DETAIL_IN_PRODUCT_DOC",
                case_name,
                path,
                f"matched forbidden implementation pattern {expression!r}",
            )

    if artifact_type in {"prd", "initiative"}:
        try:
            outcome = structured_blocks(document).get("outcome")
        except FrontmatterError as exc:
            _add(violations, "OUTCOME_INVALID", case_name, path, str(exc))
            outcome = None
        if not isinstance(outcome, Mapping):
            _add(violations, "OUTCOME_MISSING", case_name, path, "missing product-os:outcome block")

    questions = (
        _section(document.body, "Open questions")
        if artifact_type == "prd"
        else _section(document.body, "Risks and open questions")
    )
    if expected.get("open_questions_required") and not questions.strip():
        _add(
            violations,
            "OPEN_QUESTION_MISSING",
            case_name,
            path,
            "case requires a non-empty Open questions section",
        )

    if expected.get("waiver_required"):
        waiver = _section(document.body, "Evidence waiver")
        if not waiver:
            _add(violations, "EVIDENCE_WAIVER_MISSING", case_name, path, "missing evidence waiver")
        for field in ("Assumption", "Rationale", "Risk", "Review date", "Owner", "Exit condition"):
            if not re.search(rf"(?im)^[-*]\s*\*\*{re.escape(field)}:\*\*", waiver):
                _add(
                    violations,
                    "EVIDENCE_WAIVER_INCOMPLETE",
                    case_name,
                    path,
                    f"evidence waiver is missing {field}",
                )

    return violations


def evaluate_case(
    case_root: Path,
    rubric_path: Path = RUBRIC_PATH,
) -> list[Violation]:
    case = _load_yaml(case_root / "case.yaml")
    rubric = _load_yaml(rubric_path)
    case_name = str(case.get("name", case_root.name))
    expected_documents = case.get("expected_documents")
    if not isinstance(expected_documents, list):
        raise ValueError(f"case has no expected_documents list: {case_root}")

    violations: list[Violation] = []
    documents: dict[str, MarkdownDocument] = {}
    for expected in expected_documents:
        if not isinstance(expected, Mapping) or not isinstance(expected.get("file"), str):
            raise ValueError(f"invalid expected document entry in {case_root}")
        relative = str(expected["file"])
        path = case_root / "golden" / relative
        if not path.is_file():
            _add(violations, "DOCUMENT_MISSING", case_name, path.relative_to(case_root), "golden document missing")
            continue
        document = parse_markdown(path)
        documents[relative] = document
        violations.extend(_check_document(case_name, case_root, document, expected, case, rubric))

    routing = case.get("routing")
    if isinstance(routing, Mapping):
        initiative_file = str(routing.get("initiative_file"))
        initiative = documents.get(initiative_file)
        child_files = [str(value) for value in routing.get("child_files", [])]
        if initiative is None:
            _add(violations, "ROUTING_INITIATIVE_MISSING", case_name, case_root, "initiative document missing")
        else:
            relationships = initiative.metadata.get("relationships")
            actual_children = set(
                relationships.get("prds", []) if isinstance(relationships, Mapping) else []
            )
            expected_children = {
                str(documents[file].metadata.get("id"))
                for file in child_files
                if file in documents
            }
            if actual_children != expected_children:
                _add(
                    violations,
                    "INITIATIVE_CHILDREN_MISMATCH",
                    case_name,
                    initiative.path.relative_to(case_root),
                    "initiative relationships.prds must equal the expected child PRD IDs",
                )
            initiative_id = initiative.metadata.get("id")
            for child_file in child_files:
                child = documents.get(child_file)
                if child is None:
                    continue
                child_relationships = child.metadata.get("relationships")
                linked_initiative = (
                    child_relationships.get("initiative")
                    if isinstance(child_relationships, Mapping)
                    else None
                )
                if linked_initiative != initiative_id:
                    _add(
                        violations,
                        "CHILD_INITIATIVE_MISMATCH",
                        case_name,
                        child.path.relative_to(case_root),
                        "child PRD must link back to the initiative",
                    )
                if str(child.metadata.get("id")) not in initiative.body:
                    _add(
                        violations,
                        "CHILD_NOT_ROUTED_IN_BODY",
                        case_name,
                        initiative.path.relative_to(case_root),
                        f"initiative body does not reference {child.metadata.get('id')}",
                    )
            if re.search(r"^###\s+Requirements\s*$", initiative.body, re.MULTILINE):
                _add(
                    violations,
                    "CHILD_REQUIREMENTS_IN_INITIATIVE",
                    case_name,
                    initiative.path.relative_to(case_root),
                    "initiative must route barriers, not duplicate child requirements",
                )
            child_metrics: list[str] = []
            for child_file in child_files:
                child = documents.get(child_file)
                if child is None:
                    continue
                outcome = structured_blocks(child).get("outcome")
                definition = outcome.get("definition") if isinstance(outcome, Mapping) else None
                metric = definition.get("metric") if isinstance(definition, Mapping) else None
                if isinstance(metric, str):
                    child_metrics.append(metric)
            if len(child_metrics) != len(set(child_metrics)):
                _add(
                    violations,
                    "CHILD_OUTCOMES_NOT_DISTINCT",
                    case_name,
                    initiative.path.relative_to(case_root),
                    "child PRDs must own distinct outcome metrics",
                )

    return violations


def evaluate_all(cases_root: Path = CASES_ROOT) -> list[Violation]:
    violations: list[Violation] = []
    for case_root in sorted(path for path in cases_root.iterdir() if path.is_dir()):
        violations.extend(evaluate_case(case_root))
    return violations


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", nargs="*", type=Path, help="case directories; all golden cases by default")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    violations = [item for path in args.case for item in evaluate_case(path)] if args.case else evaluate_all()
    if violations:
        for violation in violations:
            print(f"FAIL [{violation.code}] {violation.case}/{violation.path}: {violation.message}")
        return 1
    case_count = len(args.case) if args.case else len([path for path in CASES_ROOT.iterdir() if path.is_dir()])
    print(f"PASS deterministic PRD-quality contract ({case_count} case(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
