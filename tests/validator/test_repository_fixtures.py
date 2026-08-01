from __future__ import annotations

from pathlib import Path

import pytest

from product_decision_os.validator import validate_workspace


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"


def test_canonical_valid_workspace_passes() -> None:
    report = validate_workspace(FIXTURES / "valid-workspace")
    assert report.exit_code == 0, [error.to_dict() for error in report.errors]


@pytest.mark.parametrize(
    ("fixture", "expected_code"),
    [
        ("duplicate-ids", "DUPLICATE_ARTIFACT_ID"),
        ("broken-reference", "BROKEN_INTERNAL_REFERENCE"),
        ("type-mismatch", "ID_TYPE_MISMATCH"),
        ("oversized-excerpt", "EVIDENCE_EXCERPT_TOO_LONG"),
        ("transcript-sized-content", "TRANSCRIPT_SIZED_CONTENT"),
        ("credential-like-content", "CREDENTIAL_LIKE_CONTENT"),
        ("stale-implementation-reference", "IMPLEMENTATION_REF_STALE"),
        ("missing-measurement-anchor", "MEASUREMENT_ANCHOR_MISSING"),
        ("unverified-executable-binding", "EXECUTABLE_BINDING_UNVERIFIED"),
    ],
)
def test_canonical_invalid_workspace_fails_for_intended_reason(fixture: str, expected_code: str) -> None:
    report = validate_workspace(FIXTURES / "invalid" / fixture)
    assert report.exit_code == 1
    assert expected_code in {error.code for error in report.errors}
