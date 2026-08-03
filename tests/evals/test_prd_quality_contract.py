from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from evals.check_prd_quality import CASES_ROOT, RUBRIC_PATH, evaluate_all, evaluate_case


def _codes(case_root: Path) -> set[str]:
    return {violation.code for violation in evaluate_case(case_root)}


def _copy_case(name: str, tmp_path: Path) -> Path:
    target = tmp_path / name
    shutil.copytree(CASES_ROOT / name, target)
    return target


def test_golden_case_set_passes_deterministic_contract() -> None:
    assert evaluate_all() == []


def test_case_set_covers_required_product_pressures() -> None:
    observed = {path.name for path in CASES_ROOT.iterdir() if path.is_dir()}
    assert observed == {
        "b2c-ux",
        "b2b-arr-demand",
        "evidence-waiver",
        "multi-prd-initiative-routing",
    }


def test_rubric_marks_model_scoring_as_external_and_uncalibrated() -> None:
    rubric = yaml.safe_load(RUBRIC_PATH.read_text(encoding="utf-8"))
    model = rubric["model_rubric"]
    assert model["execution"] == "requires_external_model_runtime_and_human_adjudication"
    assert "until calibrated" in model["proposed_gate"]["note"]


def test_references_subsection_is_optional(tmp_path: Path) -> None:
    case = _copy_case("b2c-ux", tmp_path)
    prd = case / "golden/prd.md"
    content = prd.read_text(encoding="utf-8").replace("### References\n\n", "")
    prd.write_text(content, encoding="utf-8")
    assert evaluate_case(case) == []


def test_missing_why_now_fails(tmp_path: Path) -> None:
    case = _copy_case("b2c-ux", tmp_path)
    prd = case / "golden/prd.md"
    content = prd.read_text(encoding="utf-8")
    content = content.replace("**Why now / business reality:**", "**Timing:**")
    prd.write_text(content, encoding="utf-8")
    assert "WHY_NOW_MISSING" in _codes(case)


def test_open_questions_must_be_separate(tmp_path: Path) -> None:
    case = _copy_case("b2c-ux", tmp_path)
    prd = case / "golden/prd.md"
    content = prd.read_text(encoding="utf-8").replace("## Open questions", "## Notes")
    prd.write_text(content, encoding="utf-8")
    codes = _codes(case)
    assert "SECTION_MISSING" in codes
    assert "OPEN_QUESTION_MISSING" in codes


def test_invented_metric_fails(tmp_path: Path) -> None:
    case = _copy_case("b2c-ux", tmp_path)
    prd = case / "golden/prd.md"
    content = prd.read_text(encoding="utf-8").replace(
        "baseline: to establish", "baseline: 73%"
    )
    prd.write_text(content, encoding="utf-8")
    assert "UNSUPPORTED_NUMERIC_CLAIM" in _codes(case)


def test_unknown_evidence_reference_fails(tmp_path: Path) -> None:
    case = _copy_case("b2c-ux", tmp_path)
    prd = case / "golden/prd.md"
    content = prd.read_text(encoding="utf-8").replace(
        "Both are directional sources",
        "`signal_01INVENTED001` claims broad demand. Both are directional sources",
    )
    prd.write_text(content, encoding="utf-8")
    assert "UNKNOWN_EVIDENCE_REFERENCE" in _codes(case)


def test_implementation_detail_fails(tmp_path: Path) -> None:
    case = _copy_case("b2c-ux", tmp_path)
    prd = case / "golden/prd.md"
    with prd.open("a", encoding="utf-8") as stream:
        stream.write("\n## Implementation\n\nPOST /v1/transactions/status\n")
    assert "IMPLEMENTATION_DETAIL_IN_PRODUCT_DOC" in _codes(case)


def test_incomplete_evidence_waiver_fails(tmp_path: Path) -> None:
    case = _copy_case("evidence-waiver", tmp_path)
    prd = case / "golden/prd.md"
    content = prd.read_text(encoding="utf-8")
    content = content.replace(
        "- **Risk:** the guidance may optimize an internal mental model instead of the user's actual first job.\n",
        "",
    )
    prd.write_text(content, encoding="utf-8")
    assert "EVIDENCE_WAIVER_INCOMPLETE" in _codes(case)


def test_initiative_must_route_every_child(tmp_path: Path) -> None:
    case = _copy_case("multi-prd-initiative-routing", tmp_path)
    initiative = case / "golden/initiative.md"
    content = initiative.read_text(encoding="utf-8").replace(
        "  prds: [prd_01EVALROUTE001, prd_01EVALROUTE002]",
        "  prds: [prd_01EVALROUTE001]",
    )
    initiative.write_text(content, encoding="utf-8")
    assert "INITIATIVE_CHILDREN_MISMATCH" in _codes(case)
