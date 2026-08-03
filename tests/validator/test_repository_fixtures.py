from __future__ import annotations

from pathlib import Path

import pytest

from product_os.validator import validate_workspace


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"


def test_canonical_valid_workspace_passes() -> None:
    report = validate_workspace(FIXTURES / "valid-workspace")
    assert report.exit_code == 0, [error.to_dict() for error in report.errors]


def test_valid_evidence_waiver_workspace_passes() -> None:
    report = validate_workspace(FIXTURES / "valid-waiver-workspace")
    assert report.exit_code == 0, [error.to_dict() for error in report.errors]


@pytest.mark.parametrize(
    ("fixture", "command", "expected_code"),
    [
        ("duplicate-ids", "validate", "DUPLICATE_ARTIFACT_ID"),
        ("broken-reference", "validate", "BROKEN_INTERNAL_REFERENCE"),
        ("type-mismatch", "validate", "ID_TYPE_MISMATCH"),
        ("oversized-excerpt", "validate", "EVIDENCE_EXCERPT_TOO_LONG"),
        ("transcript-sized-content", "validate", "TRANSCRIPT_SIZED_CONTENT"),
        ("credential-like-content", "validate", "CREDENTIAL_LIKE_CONTENT"),
        ("stale-implementation-reference", "validate", "IMPLEMENTATION_REF_STALE"),
        ("missing-measurement-anchor", "validate", "MEASUREMENT_ANCHOR_MISSING"),
        ("unverified-executable-binding", "validate", "EXECUTABLE_BINDING_UNVERIFIED"),
        ("stale-adapter-hash", "adapter-check", "ADAPTER_HASH_STALE"),
        ("stale-outcome-definition", "validate", "OUTCOME_BINDING_STALE"),
        ("incomplete-evidence-waiver", "validate", "SCHEMA_VALIDATION_FAILED"),
    ],
)
def test_canonical_invalid_workspace_fails_for_intended_reason(
    fixture: str, command: str, expected_code: str
) -> None:
    report = validate_workspace(FIXTURES / "invalid" / fixture, command)
    assert report.exit_code == 1
    assert expected_code in {error.code for error in report.errors}
