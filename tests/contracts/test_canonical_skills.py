from __future__ import annotations

from pathlib import Path

import yaml

from conftest import load_skill


EXPECTED_SKILLS = {
    "setup",
    "discovery",
    "initiative",
    "prd-interrogation",
    "prd-review",
    "prd-handoff",
    "decision-queue",
    "outcome-review",
    "product-update",
}


def test_all_v1_skills_are_present(repo_root: Path) -> None:
    found = {path.parent.name for path in (repo_root / "skills").glob("*/SKILL.md")}
    assert found == EXPECTED_SKILLS


def test_skills_are_versioned_and_only_declare_known_capabilities(repo_root: Path) -> None:
    contract = yaml.safe_load(
        (repo_root / "integrations/capabilities.yaml").read_text(encoding="utf-8")
    )
    known = set(contract["capabilities"])

    for path in (repo_root / "skills").glob("*/SKILL.md"):
        metadata, _ = load_skill(path)
        assert metadata["canonical_version"] == "1.0.0"
        assert metadata["name"].startswith("product-os-")
        assert set(metadata["capabilities"]) <= known
        assert "human_gates" in metadata


def test_mutating_skills_require_explicit_human_gates(repo_root: Path) -> None:
    read_only = {"decision-queue"}
    for path in (repo_root / "skills").glob("*/SKILL.md"):
        metadata, body = load_skill(path)
        if path.parent.name in read_only:
            assert metadata["human_gates"] == []
            assert "performs no write or decision" in body
        else:
            assert metadata["human_gates"], path
            normalized = body.lower()
            assert "human confirmation" in normalized or "human gate" in normalized or "human deliberately" in normalized


def test_decisions_and_approval_are_never_invented(repo_root: Path) -> None:
    discovery = (repo_root / "skills/discovery/SKILL.md").read_text(encoding="utf-8").lower()
    review = (repo_root / "skills/prd-review/SKILL.md").read_text(encoding="utf-8").lower()
    outcome = (repo_root / "skills/outcome-review/SKILL.md").read_text(encoding="utf-8").lower()

    assert "never choose for the human" in discovery
    assert "approval is `unknown` and handoff stops" in review
    assert "never choose automatically" in outcome


def test_prd_workflow_interrogates_then_reviews_then_hands_off(repo_root: Path) -> None:
    interrogation = (repo_root / "skills/prd-interrogation/SKILL.md").read_text(
        encoding="utf-8"
    ).lower()
    handoff = (repo_root / "skills/prd-handoff/SKILL.md").read_text(encoding="utf-8").lower()

    assert "do not immediately generate a prd" in interrogation
    assert "baseline/current state" in interrogation
    assert "decision rule" in interrogation
    assert "drafting does not approve or sync to linear" in interrogation
    assert "read before retrying" in handoff
    assert "never create a duplicate" in handoff
    assert "approval `unknown` is a hard stop" in handoff


def test_prd_output_contract_is_concise_modular_and_b2b_aware(repo_root: Path) -> None:
    interrogation = (repo_root / "skills/prd-interrogation/SKILL.md").read_text(
        encoding="utf-8"
    ).lower()

    assert "why now / business reality" in interrogation
    assert "open questions is a separate required section" in interrogation
    assert "references" in interrogation
    assert "omit unused optional headings completely" in interrogation
    assert "current arr" in interrogation
    assert "arr at risk" in interrogation
    assert "arr is decision context" in interrogation
    assert "external account reference and revenue band" in interrogation


def test_initiative_is_optional_and_measures_shared_outcome_separately(repo_root: Path) -> None:
    initiative = (repo_root / "skills/initiative/SKILL.md").read_text(encoding="utf-8").lower()

    assert "small product bet" in initiative
    assert "must not be forced" in initiative
    assert "shared product thesis" in initiative
    assert "distinct barriers" in initiative
    assert "child prd" in initiative
    assert "shared outcome contract" in initiative
    assert "passing all child contracts never automatically proves" in initiative
    assert "accumulated learnings" in initiative
    assert "configured reviewer must approve" in initiative


def test_setup_collects_and_previews_review_configuration(repo_root: Path) -> None:
    metadata, _ = load_skill(repo_root / "skills/setup/SKILL.md")
    setup = (repo_root / "skills/setup/SKILL.md").read_text(encoding="utf-8").lower()

    for required in (
        "default branch",
        "`provider` or `solo` review mode",
        "configured approver rule",
        "solo self-approval",
        "github_mcp` → `review.git_capability: git.review.read",
        "local_git` or `agent_native_local_git` → `review.git_capability: git.commit.read",
        "preview the exact resulting `.product-os/config.yaml`",
    ):
        assert required in setup
    assert "do not silently fall back" in setup
    assert "v1 does not declare a repository-creation capability" in setup
    assert "create a repository is an external write" not in setup
    assert set(metadata["human_gates"]) == {
        "confirm_install_origin",
        "confirm_target_repository",
        "confirm_configuration",
        "confirm_install_plan",
        "confirm_commit_or_push",
    }


def test_shared_authoring_contract_is_complete_and_used(repo_root: Path) -> None:
    shared = (repo_root / "skills/_shared/authoring-contract.md").read_text(
        encoding="utf-8"
    ).lower()
    for path in (
        "product/signals/",
        "product/patterns/",
        "product/opportunities/",
        "product/initiatives/",
        "product/prds/",
        "product/outcome-contracts/",
        "product/learnings/",
        "product/updates/",
    ):
        assert path in shared
    assert "uuid4" in shared
    assert "32 uppercase uuid4 hex" in shared
    assert "never derive an id from a title" in shared
    assert "pasted_<first-24-hex>" in shared
    assert "local_<first-24-hex>" in shared
    assert "sha256:<full-64-hex>" in shared
    assert "product-os validate <workspace>" in shared
    assert "repair only the fields named" in shared

    mutating = EXPECTED_SKILLS - {"decision-queue"}
    for skill in mutating:
        body = (repo_root / f"skills/{skill}/SKILL.md").read_text(encoding="utf-8")
        assert "../_shared/authoring-contract.md" in body, skill


def test_discovery_uses_two_commits_and_pasted_provenance(repo_root: Path) -> None:
    discovery = (repo_root / "skills/discovery/SKILL.md").read_text(encoding="utf-8").lower()
    assert "**first commit:**" in discovery
    assert "leave `decision_events` empty" in discovery
    assert "undecided-draft commit sha" in discovery
    assert "**second commit:**" in discovery
    assert "never amend the undecided draft commit" in discovery
    assert "ask for the occurrence date" in discovery
    assert "sha-256 fingerprint" in discovery


def test_prd_interrogation_is_progressive_resumable_and_routes_next(repo_root: Path) -> None:
    interrogation = (repo_root / "skills/prd-interrogation/SKILL.md").read_text(
        encoding="utf-8"
    ).lower()
    assert "ask only 1–3 related questions per turn" in interrogation
    assert "**confirmed**, **unknown**, and **blocking**" in interrogation
    assert "resumable draft checkpoint" in interrogation
    assert "exactly one recommended next question" in interrogation
    assert "## next workflow" in interrogation


def test_every_workflow_has_an_explicit_router_transition(repo_root: Path) -> None:
    for skill in EXPECTED_SKILLS:
        body = (repo_root / f"skills/{skill}/SKILL.md").read_text(encoding="utf-8")
        assert "## Next workflow" in body, skill
        assert ">" in body or "Suggested prompt:" in body or " with: “" in body, skill


def test_setup_verifies_real_client_and_live_capabilities(repo_root: Path) -> None:
    metadata, _ = load_skill(repo_root / "skills/setup/SKILL.md")
    setup = (repo_root / "skills/setup/SKILL.md").read_text(encoding="utf-8").lower()
    assert {
        "transcript.search",
        "delivery.project.read",
        "analytics.query",
        "git.review.read",
        "git.commit.read",
    } <= set(metadata["capabilities"])
    assert ".agents/skills/<skill>/skill.md" in setup
    assert ".claude/skills/<skill>/skill.md" in setup
    assert "skills/<skill>/skill.md" in setup
    assert "all nine generated route-only wrapper" in setup
    assert "static validator success alone is not connector success" in setup
    assert "one minimal safe live read for every enabled capability" in setup


def test_decision_queue_is_solo_aware_and_pm_selectable(repo_root: Path) -> None:
    metadata, body = load_skill(repo_root / "skills/decision-queue/SKILL.md")
    normalized = body.lower()
    assert {"git.review.read", "git.commit.read"} <= set(metadata["capabilities"])
    assert "select exactly its configured git capability" in normalized
    assert "compact numbered list" in normalized
    assert "no product decisions need attention right now" in normalized
    assert "accept `open n`" in normalized


def test_product_bet_and_outcome_contract_identity_rules_are_canonical(repo_root: Path) -> None:
    canonical = (repo_root / "skills/README.md").read_text(encoding="utf-8").lower()
    interrogation = (repo_root / "skills/prd-interrogation/SKILL.md").read_text(
        encoding="utf-8"
    ).lower()
    outcome = (repo_root / "skills/outcome-review/SKILL.md").read_text(encoding="utf-8").lower()

    assert "one logical product bet identity" in canonical
    assert "never mint a `bet_` id" in canonical
    assert "embedded in the owning prd or initiative by default" in canonical
    assert "do not keep a duplicated embedded copy" in canonical
    assert "never mint a separate `bet_` artifact" in interrogation
    assert "passing child contracts never proves the shared outcome automatically" in outcome


def test_privacy_measurement_and_update_guardrails_are_explicit(repo_root: Path) -> None:
    discovery = (repo_root / "skills/discovery/SKILL.md").read_text(encoding="utf-8").lower()
    outcome = (repo_root / "skills/outcome-review/SKILL.md").read_text(encoding="utf-8").lower()
    update = (repo_root / "skills/product-update/SKILL.md").read_text(encoding="utf-8").lower()

    assert "never commit a full transcript" in discovery
    assert "maximum length of 500 characters" in discovery
    assert "never infer the anchor from linear completion" in outcome
    assert "make no success or failure claim" in outcome
    assert "every material claim" in update
    assert "block publication" in update


def test_downstream_workflows_verify_the_configured_approved_version(repo_root: Path) -> None:
    for skill in ("outcome-review", "product-update"):
        metadata, body = load_skill(repo_root / f"skills/{skill}/SKILL.md")
        normalized = body.lower()
        assert {"git.review.read", "git.commit.read"} <= set(metadata["capabilities"])
        assert "exactly the configured git capability" in normalized
        assert "never fall back between review modes" in normalized
