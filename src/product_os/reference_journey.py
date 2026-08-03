#!/usr/bin/env python3
"""Run the deterministic clean-install-to-learning reference journey.

This runner proves the repository-controlled path without live provider credentials.
It installs Product OS into a new Git repository, materializes the technical
reference fixture through real commits, replaces fixture-only versions with reachable
commit SHAs, and runs final validation and smoke checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from product_os.frontmatter import MarkdownDocument, parse_markdown  # noqa: E402
from product_os.validator import validate_workspace  # noqa: E402

from .installer import apply_plan, plan_install, write_plan  # noqa: E402
from .manifest import verify  # noqa: E402

REFERENCE_FIXTURE_ROOT = REPOSITORY_ROOT / "tests" / "fixtures" / "reference-journey"
CLIENTS = ("codex", "claude-code", "openclaw")


class JourneyError(RuntimeError):
    """Raised when the reference journey cannot prove a required transition."""


def _git(workspace: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(workspace), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _commit(workspace: Path, message: str, *, synthetic_approval: bool = False) -> str:
    _git(workspace, "add", ".")
    if synthetic_approval:
        _git(
            workspace,
            "commit",
            "-q",
            "-m",
            message,
            "-m",
            "Product-Approval: explicit",
        )
    else:
        _git(workspace, "commit", "-q", "-m", message)
    sha = _git(workspace, "rev-parse", "HEAD")
    if len(sha) != 40:
        raise JourneyError(f"expected a full commit SHA after {message!r}")
    return sha


def _write_document(path: Path, metadata: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = yaml.safe_dump(
        metadata,
        sort_keys=False,
        allow_unicode=True,
        width=1_000,
    ).rstrip()
    path.write_text(f"---\n{frontmatter}\n---\n{body.lstrip()}", encoding="utf-8")


def _documents(fixture: Path) -> list[MarkdownDocument]:
    return [parse_markdown(path) for path in sorted((fixture / "product").glob("*/*.md"))]


def _copy_external_fixture(fixture: Path, target: Path) -> None:
    for directory in ("external", "inputs"):
        source = fixture / directory
        if source.is_dir():
            shutil.copytree(source, target / directory)


def _rewrite_external_versions(target: Path, approved_sha: str) -> None:
    version_keys = {
        "approved_version",
        "based_on_prd_version",
        "git_sha",
        "synced_from_version",
        "version",
    }

    def rewrite(value: Any, key: str | None = None) -> Any:
        if isinstance(value, dict):
            return {item_key: rewrite(item_value, item_key) for item_key, item_value in value.items()}
        if isinstance(value, list):
            return [rewrite(item, key) for item in value]
        if key in version_keys and isinstance(value, str) and len(value) in {40, 64}:
            return approved_sha
        return value

    for path in sorted((target / "external").rglob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        path.write_text(yaml.safe_dump(rewrite(document), sort_keys=False), encoding="utf-8")


def _rewrite_learning_review_version(target: Path, learning_id: str, learning_sha: str) -> None:
    path = target / "external" / "git" / "reviews.yaml"
    if not path.is_file():
        return
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    reviews = document.get("reviews") if isinstance(document, dict) else None
    if not isinstance(reviews, list):
        raise JourneyError("external Git review fixture has no reviews array")
    for review in reviews:
        if isinstance(review, dict) and review.get("artifact_id") == learning_id:
            review["version"] = learning_sha
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def _configured_fixture(fixture: Path, destination: Path, client: str) -> Path:
    config = yaml.safe_load((fixture / ".product-os" / "config.yaml").read_text(encoding="utf-8"))
    config["selected_client"] = client
    config["review"] = {
        "mode": "solo",
        "approver_rule": {"initiative": "self", "prd": "self"},
        "solo_approval": {
            "allowed": True,
            "commit_trailer": "Product-Approval: explicit",
        },
        "git_capability": "git.commit.read",
    }
    destination.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return destination


def _actual_review_state(fixture: Path, approved_versions: dict[str, str]) -> dict[str, Any]:
    state = yaml.safe_load(
        (fixture / ".product-os" / "review-state.yaml").read_text(encoding="utf-8")
    )
    approved = state.get("approved_artifacts")
    if not isinstance(approved, dict) or not approved:
        raise JourneyError("reference fixture review-state has no approved_artifacts")
    for artifact_id in list(approved):
        if artifact_id not in approved_versions:
            del approved[artifact_id]
            continue
        raw_entry = approved[artifact_id]
        if not isinstance(raw_entry, dict):
            raise JourneyError(f"review-state entry for {artifact_id} is not an object")
        raw_entry.pop("synthetic", None)
        raw_entry["synthetic_reference"] = True
        raw_entry["approved_by"] = "synthetic-reference-runner"
        raw_entry["approved_version"] = approved_versions[artifact_id]
        provenance = raw_entry.setdefault("provenance", {})
        provenance.pop("provider_reference", None)
        provenance["git_sha"] = approved_versions[artifact_id]
        provenance["verification_mode"] = "solo_commit"
        provenance["verified_by"] = "synthetic-reference-runner"
        provenance["commit_trailer_verified"] = True
    return state


def _materialize_product_history(fixture: Path, target: Path) -> dict[str, str]:
    documents = _documents(fixture)
    by_type: dict[str, list[MarkdownDocument]] = {}
    for document in documents:
        by_type.setdefault(str(document.metadata["type"]), []).append(document)

    required = {
        "signal": 4,
        "pattern": 2,
        "opportunity": 1,
        "initiative": 1,
        "prd": 4,
        "learning": 1,
        "product_update": 1,
    }
    observed = {kind: len(by_type.get(kind, [])) for kind in required}
    if observed != required:
        raise JourneyError(f"reference graph is incomplete: expected {required}, observed {observed}")

    for kind in ("signal", "pattern"):
        for document in by_type[kind]:
            relative = document.path.relative_to(fixture)
            _write_document(target / relative, copy.deepcopy(document.metadata), document.body)

    opportunity = by_type["opportunity"][0]
    opportunity_draft = copy.deepcopy(opportunity.metadata)
    final_opportunity_events = copy.deepcopy(opportunity_draft["decision_events"])
    opportunity_draft["decision_events"] = []
    opportunity_path = target / opportunity.path.relative_to(fixture)
    _write_document(opportunity_path, opportunity_draft, opportunity.body)
    evidence_sha = _commit(target, "docs: capture trading evidence and opportunity draft")

    final_opportunity_events[-1]["based_on_version"] = evidence_sha
    opportunity_draft["decision_events"] = final_opportunity_events
    _write_document(opportunity_path, opportunity_draft, opportunity.body)
    pursue_sha = _commit(target, "docs: pursue best-in-class trading experience")

    for document in by_type["initiative"]:
        relative = document.path.relative_to(fixture)
        _write_document(target / relative, copy.deepcopy(document.metadata), document.body)

    final_prd_metadata: dict[Path, dict[str, Any]] = {}
    for document in by_type["prd"]:
        relative = document.path.relative_to(fixture)
        metadata = copy.deepcopy(document.metadata)
        final_prd_metadata[relative] = copy.deepcopy(metadata)
        metadata["implementation_refs"] = []
        metadata["delivery_refs"] = []
        _write_document(target / relative, metadata, document.body)
    approved_sha = _commit(
        target,
        "test: self-attest synthetic initiative and child PRDs",
        synthetic_approval=True,
    )

    for document in by_type["prd"]:
        relative = document.path.relative_to(fixture)
        metadata = final_prd_metadata[relative]
        for reference in metadata.get("implementation_refs", []):
            reference["based_on_prd_version"] = approved_sha
        for reference in metadata.get("delivery_refs", []):
            if "synced_from_version" in reference:
                reference["synced_from_version"] = approved_sha
        _write_document(target / relative, metadata, document.body)

    approved_artifact_ids = {
        str(opportunity.metadata["id"]),
        *(str(document.metadata["id"]) for document in by_type["initiative"]),
        *(str(document.metadata["id"]) for document in by_type["prd"]),
    }
    approved_versions = {artifact_id: approved_sha for artifact_id in approved_artifact_ids}
    state = _actual_review_state(fixture, approved_versions)
    state_path = target / ".product-os" / "review-state.yaml"
    state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
    _copy_external_fixture(fixture, target)
    _rewrite_external_versions(target, approved_sha)
    handoff_sha = _commit(target, "test: record synthetic delivery handoff")

    learning = by_type["learning"][0]
    learning_metadata = copy.deepcopy(learning.metadata)
    final_learning_events = copy.deepcopy(learning_metadata["decision_events"])
    learning_metadata["decision_events"] = []
    _write_document(target / learning.path.relative_to(fixture), learning_metadata, learning.body)
    measurement_sha = _commit(target, "docs: stage synthetic outcome review")

    final_learning_events[-1]["based_on_version"] = measurement_sha
    learning_metadata["decision_events"] = final_learning_events
    _write_document(target / learning.path.relative_to(fixture), learning_metadata, learning.body)
    learning_sha = _commit(
        target,
        "test: self-attest synthetic outcome decision",
        synthetic_approval=True,
    )

    approved_versions[str(learning.metadata["id"])] = learning_sha
    state = _actual_review_state(fixture, approved_versions)
    state_path.write_text(yaml.safe_dump(state, sort_keys=False), encoding="utf-8")
    _rewrite_learning_review_version(
        target,
        str(learning.metadata["id"]),
        learning_sha,
    )

    update = by_type["product_update"][0]
    update_metadata = copy.deepcopy(update.metadata)
    for claim in update_metadata.get("claims", []):
        for reference in claim.get("source_references", []):
            if reference.get("kind") == "artifact":
                reference["version"] = learning_sha
    _write_document(target / update.path.relative_to(fixture), update_metadata, update.body)
    final_sha = _commit(target, "docs: publish reference product update")

    return {
        "evidence": evidence_sha,
        "pursue": pursue_sha,
        "approved": approved_sha,
        "handoff": handoff_sha,
        "measurement": measurement_sha,
        "learning": learning_sha,
        "final": final_sha,
    }


def run_journey(target: Path, client: str) -> dict[str, Any]:
    if client not in CLIENTS:
        raise JourneyError(f"unknown client {client!r}")
    if target.exists() and any(target.iterdir()):
        raise JourneyError(f"target must be absent or empty: {target}")
    target.mkdir(parents=True, exist_ok=True)
    _git(target, "init", "-q", "-b", "main")
    _git(target, "config", "user.name", "Product OS Reference")
    _git(target, "config", "user.email", "reference@example.invalid")

    manifest_problems = verify(REPOSITORY_ROOT)
    if manifest_problems:
        raise JourneyError("release manifest verification failed: " + "; ".join(manifest_problems))

    with tempfile.TemporaryDirectory(prefix="product-os-reference-") as temporary:
        temporary_root = Path(temporary)
        config_path = _configured_fixture(
            REFERENCE_FIXTURE_ROOT,
            temporary_root / "config.yaml",
            client,
        )
        plan_path = temporary_root / "install-plan.json"
        plan = plan_install(
            REPOSITORY_ROOT,
            target,
            client,
            config_path,
            allow_unpublished_local=True,
        )
        write_plan(plan, plan_path)
        confirmed_hash = json.loads(plan_path.read_text(encoding="utf-8"))["plan_hash"]
        if confirmed_hash != plan.plan_hash:
            raise JourneyError("saved install plan hash changed before apply")
        apply_plan(plan)

    install_sha = _commit(target, "chore: install Product OS")
    history = _materialize_product_history(REFERENCE_FIXTURE_ROOT, target)

    validation = validate_workspace(target, command="validate")
    smoke = validate_workspace(target, command="smoke-test")
    if not validation.ok or not smoke.ok:
        errors = [item.to_dict() for item in (*validation.errors, *smoke.errors)]
        raise JourneyError("final workspace did not validate: " + json.dumps(errors, sort_keys=True))

    final_documents = [parse_markdown(path) for path in sorted((target / "product").glob("*/*.md"))]
    initiative = next(
        document for document in final_documents if document.metadata.get("type") == "initiative"
    )
    learning = next(
        document for document in final_documents if document.metadata.get("type") == "learning"
    )
    child_prds = initiative.metadata.get("child_prd_ids", [])
    final_decision = learning.metadata.get("decision_events", [])[-1].get("choice")
    if len(child_prds) != 4 or final_decision not in {"scale", "iterate", "complete"}:
        raise JourneyError("reference journey did not close the intended multi-PRD learning loop")

    return {
        "status": "passed",
        "scope": "deterministic_offline_reference",
        "client": client,
        "target": str(target.resolve()),
        "install_commit": install_sha,
        "history": history,
        "artifacts": len(final_documents),
        "child_prds": len(child_prds),
        "final_decision": final_decision,
        "validation": {
            "errors": len(validation.errors),
            "warnings": len(validation.warnings),
        },
        "smoke_test": {
            "errors": len(smoke.errors),
            "warnings": len(smoke.warnings),
        },
        "not_proven": [
            "live Granola authorization and retrieval",
            "live configured delivery-provider mutation (Linear in reference V1)",
            "live analytics query execution",
            "live Git review provider identity",
            "human approval or self-attestation",
            "agent skill execution and input-to-artifact transformation",
            "LLM output quality across agent providers",
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, help="absent or empty destination; temporary by default")
    parser.add_argument("--client", choices=CLIENTS, default="codex")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.target:
            result = run_journey(args.target, args.client)
        else:
            with tempfile.TemporaryDirectory(prefix="product-os-e2e-") as temporary:
                result = run_journey(Path(temporary) / "workspace", args.client)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (JourneyError, OSError, subprocess.CalledProcessError, yaml.YAMLError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
