"""Resolve the clarity population from repository publication policy."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def glob_files(patterns: list[str]) -> set[str]:
    found: set[str] = set()
    for pattern in patterns:
        found.update(rel(path) for path in ROOT.glob(pattern) if path.is_file())
    return found


def path_is_under(path: str, declared: str) -> bool:
    declared = declared.rstrip("/")
    return path == declared or path.startswith(declared + "/")


def publication_contract(contract: dict) -> dict:
    return load(ROOT / contract["scope"]["publication_contract"])


def publication_surface(path: str, publication: dict) -> str | None:
    matches = [
        item for item in publication.get("paths", [])
        if path_is_under(path, item["path"])
    ]
    if not matches:
        return None
    return max(matches, key=lambda item: len(item["path"]))["surface"]


def scanned_candidates(contract: dict) -> set[str]:
    scope = contract["scope"]
    return (
        glob_files(scope["candidate_include"])
        - glob_files(scope.get("candidate_exclude", []))
    )


def scope_errors(contract: dict) -> list[str]:
    publication = publication_contract(contract)
    known = set(publication.get("surfaces", {}))
    errors = []
    for path in sorted(scanned_candidates(contract)):
        surface = publication_surface(path, publication)
        if surface is None:
            errors.append(
                f"{path}: human-facing text has no publication-surface classification"
            )
        elif surface not in known:
            errors.append(f"{path}: unknown publication surface {surface!r}")
    return errors


def clarity_candidates(contract: dict) -> set[str]:
    publication = publication_contract(contract)
    included = set(contract["scope"]["include_surfaces"])
    return {
        path for path in scanned_candidates(contract)
        if publication_surface(path, publication) in included
    }


def exemption_map(contract: dict) -> dict[str, str]:
    candidates = clarity_candidates(contract)
    exemptions: dict[str, str] = {}
    for rule in contract["scope"].get("exemptions", []):
        for path in glob_files(rule["include"]) & candidates:
            exemptions[path] = rule["reason"].strip()
    return exemptions


def eligible(contract: dict) -> set[str]:
    return clarity_candidates(contract) - set(exemption_map(contract))


def campaigns(contract: dict) -> dict[str, list[str]]:
    remaining = set(eligible(contract))
    grouped: dict[str, list[str]] = {}
    for name in contract["campaign_order"]:
        campaign = contract["campaigns"][name]
        matched = (
            glob_files(campaign["include"])
            - glob_files(campaign.get("exclude", []))
        )
        grouped[name] = sorted(remaining & matched)
        remaining -= set(grouped[name])
    grouped["_unassigned"] = sorted(remaining)
    return grouped


def default_basis(contract: dict, path: str) -> list[str]:
    exact = contract.get("basis_by_path", {})
    if path in exact:
        return exact[path]
    for rule in contract.get("basis_by_pattern", []):
        if path in glob_files(rule["include"]):
            return rule["basis"]
    return []
