#!/usr/bin/env python3
"""Measure and record repository clarity coverage."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "clarity.json"
DIGEST_PREFIX = "sha256:"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def digest(path: Path) -> str:
    return DIGEST_PREFIX + sha256(path.read_bytes()).hexdigest()


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
    path = ROOT / contract["scope"]["publication_contract"]
    return load(path)


def publication_surface(path: str, publication: dict) -> str | None:
    matches = [
        item
        for item in publication.get("paths", [])
        if path_is_under(path, item["path"])
    ]
    if not matches:
        return None
    matches.sort(key=lambda item: len(item["path"]), reverse=True)
    return matches[0]["surface"]


def scanned_candidates(contract: dict) -> set[str]:
    scope = contract["scope"]
    included = glob_files(scope["candidate_include"])
    excluded = glob_files(scope.get("candidate_exclude", []))
    return included - excluded


def scope_errors(contract: dict) -> list[str]:
    publication = publication_contract(contract)
    known_surfaces = set(publication.get("surfaces", {}))
    errors: list[str] = []
    for path in sorted(scanned_candidates(contract)):
        surface = publication_surface(path, publication)
        if surface is None:
            errors.append(
                f"{path}: human-facing text has no publication-surface classification"
            )
        elif surface not in known_surfaces:
            errors.append(f"{path}: unknown publication surface {surface!r}")
    return errors


def clarity_candidates(contract: dict) -> set[str]:
    publication = publication_contract(contract)
    included_surfaces = set(contract["scope"]["include_surfaces"])
    return {
        path
        for path in scanned_candidates(contract)
        if publication_surface(path, publication) in included_surfaces
    }


def exemption_map(contract: dict) -> dict[str, str]:
    candidates = clarity_candidates(contract)
    exemptions: dict[str, str] = {}
    for rule in contract["scope"].get("exemptions", []):
        reason = rule["reason"].strip()
        for path in glob_files(rule["include"]) & candidates:
            exemptions[path] = reason
    return exemptions


def eligible(contract: dict) -> set[str]:
    return clarity_candidates(contract) - set(exemption_map(contract))


def campaign_files(contract: dict) -> dict[str, list[str]]:
    remaining = set(eligible(contract))
    grouped: dict[str, list[str]] = {}
    for name in contract["campaign_order"]:
        campaign = contract["campaigns"][name]
        matched = glob_files(campaign["include"])
        matched -= glob_files(campaign.get("exclude", []))
        selected = sorted(remaining & matched)
        grouped[name] = selected
        remaining -= set(selected)
    grouped["_unassigned"] = sorted(remaining)
    return grouped


def campaigns(contract: dict) -> dict[str, list[str]]:
    return campaign_files(contract)


def coverage_path(contract: dict) -> Path:
    return ROOT / contract["coverage_file"]


def coverage(contract: dict) -> dict:
    path = coverage_path(contract)
    if path.exists():
        return load(path)
    return {
        "schema": "soveraeign-clarity-coverage/v1",
        "skill": contract["skill"],
        "reviews": {},
    }


def review_state(path: str, review: dict | None) -> str:
    if review is None:
        return "UNCHECKED"
    artifact = ROOT / path
    if not artifact.is_file() or digest(artifact) != review.get("artifact_digest"):
        return "TEXT_STALE"
    for basis in review.get("basis", []):
        source = ROOT / basis["path"]
        if not source.is_file() or digest(source) != basis.get("digest"):
            return "BASIS_STALE"
    return "CURRENT"


def state_map(contract: dict, record: dict) -> dict[str, str]:
    reviews = record.get("reviews", {})
    exemptions = exemption_map(contract)
    states = {path: "EXEMPT" for path in sorted(exemptions)}
    states.update(
        {
            path: review_state(path, reviews.get(path))
            for path in sorted(eligible(contract))
        }
    )
    return dict(sorted(states.items()))


def pct(a: int, b: int) -> float:
    return 100.0 if b == 0 else 100.0 * a / b


def status(contract: dict, record: dict) -> None:
    reviews = record.get("reviews", {})
    grouped = campaigns(contract)
    states = state_map(contract, record)
    print("Clarity coverage\n")
    for name in contract["campaign_order"]:
        paths = grouped[name]
        current = sum(states[path] == "CURRENT" for path in paths)
        reviewed = sum(path in reviews for path in paths)
        print(
            f"{name:<12} {current:>3} current / {reviewed:>3} reviewed / "
            f"{len(paths):>3} eligible"
        )
    if grouped["_unassigned"]:
        print(f"{'UNASSIGNED':<12} {len(grouped['_unassigned']):>3}")

    eligible_paths = eligible(contract)
    total = len(eligible_paths)
    reviewed = sum(path in reviews for path in eligible_paths)
    current = sum(states[path] == "CURRENT" for path in eligible_paths)
    stale = reviewed - current
    exempt = len(exemption_map(contract))
    print("")
    print(f"coverage         {pct(reviewed, total):6.1f}%")
    print(f"freshness        {pct(current, reviewed):6.1f}%")
    print(f"current coverage {pct(current, total):6.1f}%")
    print("")
    print(f"CURRENT     {current:>4}")
    print(f"STALE       {stale:>4}")
    print(f"UNCHECKED   {total - reviewed:>4}")
    print(f"EXEMPT      {exempt:>4}")


def valid_digest(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith(DIGEST_PREFIX):
        return False
    body = value[len(DIGEST_PREFIX):]
    return len(body) == 64 and all(char in "0123456789abcdef" for char in body)


def path_matches_any(path: str, patterns: list[str]) -> bool:
    return path in glob_files(patterns)


def default_basis(contract: dict, path: str) -> list[str]:
    exact = contract.get("basis_by_path", {})
    if path in exact:
        return exact[path]
    for rule in contract.get("basis_by_pattern", []):
        if path_matches_any(path, rule["include"]):
            return rule["basis"]
    return []


def registry_errors(contract: dict, record: dict) -> list[str]:
    errors: list[str] = []
    errors.extend(scope_errors(contract))
    grouped = campaigns(contract)
    for path in grouped["_unassigned"]:
        errors.append(f"{path}: clarity candidate is not assigned to a campaign")

    if record.get("schema") != "soveraeign-clarity-coverage/v1":
        errors.append("coverage schema must be soveraeign-clarity-coverage/v1")
    if record.get("skill") != contract["skill"]:
        errors.append(f"coverage skill must be {contract['skill']}")
    reviews = record.get("reviews")
    if not isinstance(reviews, dict):
        return errors + ["reviews must be an object keyed by repository path"]

    allowed = eligible(contract)
    exemptions = exemption_map(contract)
    for path, review in reviews.items():
        if path not in allowed:
            if path in exemptions:
                errors.append(f"{path}: exempt artifacts must not carry review receipts")
            else:
                errors.append(f"{path}: review is outside the declared clarity scope")
            continue
        if not isinstance(review, dict):
            errors.append(f"{path}: review must be an object")
            continue
        if not valid_digest(review.get("artifact_digest")):
            errors.append(f"{path}: artifact_digest is not sha256:<64-hex>")
        if not isinstance(review.get("changed"), bool):
            errors.append(f"{path}: changed must be true or false")
        basis = review.get("basis", [])
        if not isinstance(basis, list):
            errors.append(f"{path}: basis must be a list")
            continue
        expected = default_basis(contract, path)
        actual = [item.get("path") for item in basis if isinstance(item, dict)]
        if expected and actual != expected:
            errors.append(f"{path}: basis must be {expected!r}, got {actual!r}")
        for item in basis:
            if not isinstance(item, dict):
                errors.append(f"{path}: basis entries must be objects")
                continue
            source = item.get("path")
            if not isinstance(source, str) or not (ROOT / source).is_file():
                errors.append(f"{path}: missing basis file {source!r}")
            if not valid_digest(item.get("digest")):
                errors.append(f"{path}: invalid digest for basis {source!r}")
    return errors


def do_scope(contract: dict) -> int:
    errors = scope_errors(contract)
    exemptions = exemption_map(contract)
    grouped = campaigns(contract)
    print("Clarity scope\n")
    print(f"scanned       {len(scanned_candidates(contract)):>4}")
    print(f"current prose {len(clarity_candidates(contract)):>4}")
    print(f"eligible      {len(eligible(contract)):>4}")
    print(f"exempt        {len(exemptions):>4}")
    print(f"unassigned    {len(grouped['_unassigned']):>4}")
    if exemptions:
        print("\nExemptions")
        for path in sorted(exemptions):
            print(f"- {path}: {exemptions[path]}")
    if errors:
        print("\nScope errors")
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    if grouped["_unassigned"]:
        print("\nUnassigned")
        for path in grouped["_unassigned"]:
            print(f"ERROR: {path}")
        return 1
    print("\nPASS: every current prose candidate is eligible or explicitly exempt")
    return 0


def do_next(contract: dict, record: dict) -> int:
    states = state_map(contract, record)
    grouped = campaigns(contract)
    for wanted in ("TEXT_STALE", "BASIS_STALE", "UNCHECKED"):
        for campaign in contract["campaign_order"]:
            for path in grouped[campaign]:
                if states[path] == wanted:
                    print(path)
                    print(f"state: {wanted}")
                    print(f"campaign: {campaign}")
                    return 0
    print("All eligible clarity reviews are current.")
    return 0


def do_record(
    contract: dict,
    record: dict,
    path_text: str,
    basis_args: list[str] | None,
    changed: bool,
) -> int:
    artifact = (ROOT / path_text).resolve()
    try:
        path = artifact.relative_to(ROOT).as_posix()
    except ValueError:
        raise SystemExit("path must stay inside the repository")
    if path in exemption_map(contract):
        raise SystemExit(f"{path} is explicitly exempt from clarity review")
    if path not in eligible(contract):
        raise SystemExit(f"{path} is outside the declared clarity scope")
    if not artifact.is_file():
        raise SystemExit(f"{path} does not exist")
    basis_paths = basis_args if basis_args is not None else default_basis(contract, path)
    basis = []
    for source in basis_paths:
        target = ROOT / source
        if not target.is_file():
            raise SystemExit(f"basis file does not exist: {source}")
        basis.append({"path": source, "digest": digest(target)})
    record.setdefault("reviews", {})[path] = {
        "artifact_digest": digest(artifact),
        "basis": basis,
        "changed": changed,
    }
    save(coverage_path(contract), record)
    print(f"recorded {path}")
    print(f"basis: {len(basis)}")
    print(f"changed: {'yes' if changed else 'no'}")
    return 0


def stale_items(contract: dict, record: dict) -> list[str]:
    return [
        f"{path}: {state}"
        for path, state in state_map(contract, record).items()
        if state in {"TEXT_STALE", "BASIS_STALE"}
    ]


def do_check(contract: dict, record: dict) -> int:
    errors = registry_errors(contract, record)
    stale = stale_items(contract, record)
    for error in errors:
        print(f"ERROR: {error}")
    for item in stale:
        print(f"STALE: {item}")
    if errors or stale:
        return 1
    print("PASS: clarity scope and receipts are well-formed and current")
    return 0


def do_gate(contract: dict, record: dict) -> int:
    if do_check(contract, record):
        return 1
    states = state_map(contract, record)
    incomplete = [
        f"{path}: {state}"
        for path, state in states.items()
        if state not in {"CURRENT", "EXEMPT"}
    ]
    if incomplete:
        for item in incomplete:
            print(f"INCOMPLETE: {item}")
        return 1
    print("PASS: clarity current coverage is 100%")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    status_cmd = commands.add_parser("status", help="show coverage and freshness")
    status_cmd.add_argument("--json", action="store_true")
    commands.add_parser("scope", help="show and validate the clarity denominator")
    commands.add_parser("next", help="print the next stale or unchecked artifact")
    commands.add_parser("check", help="validate scope and refuse stale receipts")
    commands.add_parser("gate", help="require 100% current clarity coverage")
    record = commands.add_parser("record", help="record a completed clarity review")
    record.add_argument("path")
    record.add_argument("--basis", action="append")
    record.add_argument("--changed", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    contract = load(CONTRACT_PATH)
    record = coverage(contract)
    if args.command == "status":
        if args.json:
            print(json.dumps(state_map(contract, record), indent=2, sort_keys=True))
        else:
            status(contract, record)
        return 0
    if args.command == "scope":
        return do_scope(contract)
    if args.command == "next":
        return do_next(contract, record)
    if args.command == "record":
        return do_record(contract, record, args.path, args.basis, args.changed)
    if args.command == "check":
        return do_check(contract, record)
    if args.command == "gate":
        return do_gate(contract, record)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
