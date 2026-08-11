from __future__ import annotations

from pathlib import Path
import shutil

import yaml

from product_os.adapters import canonical_source_digest, generate_adapters

CLIENTS = {
    "codex": ".agents/skills",
    "claude-code": ".claude/skills",
    "openclaw": "skills",
}

ROUTES = {
    "product-os-setup": "setup",
    "product-os-discovery": "discovery",
    "product-os-initiative": "initiative",
    "product-os-prd": "prd",
    "product-os-decision-queue": "decision-queue",
    "product-os-outcome-review": "outcome-review",
    "product-os-product-update": "product-update",
}


def test_client_adapters_have_matching_generated_metadata(repo_root: Path) -> None:
    expected_hash = canonical_source_digest(repo_root)
    seen_hashes = set()

    for client, install_location in CLIENTS.items():
        directory = repo_root / "adapters" / client
        manifest = yaml.safe_load((directory / "manifest.yaml").read_text(encoding="utf-8"))
        instructions = (directory / "ADAPTER.md").read_text(encoding="utf-8")

        assert manifest["generated"] is True
        assert manifest["client"] == client
        assert manifest["canonical_source"]["version"] == "1.0.0"
        assert manifest["canonical_source"]["hash_algorithm"] == "sha256"
        assert manifest["canonical_source"]["content_hash"] == expected_hash
        assert manifest["projection"]["client_skill_location"] == install_location
        assert manifest["projection"]["canonical_skills"] == "../../skills"
        assert manifest["projection"]["capability_mappings"] == "../../integrations"
        assert manifest["projection"]["wrapper_root"] == "../_shared/skills"
        assert {item["name"] for item in manifest["projections"]} == set(ROUTES)
        assert manifest["safety"] == {
            "embeds_credentials": False,
            "implements_mcp": False,
            "network_client": False,
            "generated_files_are_source_of_truth": False,
        }
        assert f"canonical_sha256={expected_hash}" in instructions
        seen_hashes.add(manifest["canonical_source"]["content_hash"])

    assert seen_hashes == {expected_hash}


def test_manifests_define_exact_source_wrapper_and_destination(repo_root: Path) -> None:
    for client, install_root in CLIENTS.items():
        manifest = yaml.safe_load(
            (repo_root / f"adapters/{client}/manifest.yaml").read_text(encoding="utf-8")
        )
        assert len(manifest["projections"]) == len(ROUTES)
        for item in manifest["projections"]:
            canonical_dir = ROUTES[item["name"]]
            assert item["canonical_source"] == f".product-os/skills/{canonical_dir}/SKILL.md"
            assert item["wrapper_source"] == f"adapters/_shared/skills/{item['name']}/SKILL.md"
            assert item["destination"] == f"{install_root}/{item['name']}/SKILL.md"
            assert (repo_root / item["wrapper_source"]).is_file()


def test_simulated_client_install_discovers_route_only_skills(
    repo_root: Path, tmp_path: Path
) -> None:
    for client in CLIENTS:
        workspace = tmp_path / client
        shutil.copytree(repo_root / "skills", workspace / ".product-os/skills")
        manifest = yaml.safe_load(
            (repo_root / f"adapters/{client}/manifest.yaml").read_text(encoding="utf-8")
        )
        for item in manifest["projections"]:
            destination = workspace / item["destination"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repo_root / item["wrapper_source"], destination)

        discovered = sorted((workspace / CLIENTS[client]).glob("*/SKILL.md"))
        assert len(discovered) == len(ROUTES)
        for wrapper in discovered:
            text = wrapper.read_text(encoding="utf-8")
            _, frontmatter, body = text.split("---", 2)
            metadata = yaml.safe_load(frontmatter)
            canonical_dir = ROUTES[metadata["name"]]
            canonical = workspace / f".product-os/skills/{canonical_dir}/SKILL.md"
            assert canonical.is_file()
            assert f".product-os/skills/{canonical_dir}/SKILL.md" in body
            assert "sole workflow source" in body
            assert "## Procedure" not in body
            assert "human_gates:" not in body


def test_adapters_are_static_instructions_not_runtime_code(repo_root: Path) -> None:
    files = [path for path in (repo_root / "adapters").rglob("*") if path.is_file()]
    assert files
    assert {path.suffix for path in files} <= {".md", ".yaml"}

    for client in CLIENTS:
        instructions = (repo_root / f"adapters/{client}/ADAPTER.md").read_text(
            encoding="utf-8"
        ).lower()
        assert "already" in instructions
        assert "read-only" in instructions
        assert "custom mcp" in instructions


def test_wrapper_content_is_client_neutral(repo_root: Path) -> None:
    for name in ROUTES:
        assert (repo_root / f"adapters/_shared/skills/{name}/SKILL.md").is_file()


def test_adapter_generation_is_idempotent(repo_root: Path, tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    for directory in ("skills", "integrations", "adapters"):
        shutil.copytree(repo_root / directory, checkout / directory)

    assert generate_adapters(checkout) == []
    assert generate_adapters(checkout, check=True) == []
