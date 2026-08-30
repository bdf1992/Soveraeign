#!/usr/bin/env python3
"""Measure and record repository clarity coverage."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from sovclarity.scope import (
    campaigns,
    clarity_candidates,
    default_basis,
    eligible,
    exemption_map,
    scanned_candidates,
    scope_errors,
)

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
    states = {path: "EXEMPT" for path in sorted(exemption_map(contract))}
    states.update({
        path: review_state(path, reviews.get(path))
        for path in sorted(eligible(contract))
    })
    return dict(sorted(states.items()))

def pct(a: int, b: int) -> float:
    return 100.0 if b == 0 else 100.0 * a / b

def status(contract: dict, record: dict) -> None:
    reviews, grouped = record.get("reviews", {}), campaigns(contract)
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
    paths = eligible(contract)
    reviewed = sum(path in reviews for path in paths)
    current = sum(states[path] == "CURRENT" for path in paths)
    print("")
    print(f"coverage         {pct(reviewed, len(paths)):6.1f}%")
    print(f"freshness        {pct(current, reviewed):6.1f}%")
    print(f"current coverage {pct(current, len(paths)):6.1f}%")
    print("")
    print(f"CURRENT     {current:>4}")
    print(f"STALE       {reviewed - current:>4}")
    print(f"UNCHECKED   {len(paths) - reviewed:>4}")
    print(f"EXEMPT      {len(exemption_map(contract)):>4}")

def valid_digest(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith(DIGEST_PREFIX):
        return False
    body = value[len(DIGEST_PREFIX):]
    return len(body) == 64 and all(char in "0123456789abcdef" for char in body)

def registry_errors(contract: dict, record: dict) -> list[str]:
    errors = list(scope_errors(contract))
    errors.extend(
        f"{path}: clarity candidate is not assigned to a campaign"
        for path in campaigns(contract)["_unassigned"]
    )
    if record.get("schema") != "soveraeign-clarity-coverage/v1":
        errors.append("coverage schema must be soveraeign-clarity-coverage/v1")
    if record.get("skill") != contract["skill"]:
        errors.append(f"coverage skill must be {contract['skill']}")
    reviews = record.get("reviews")
    if not isinstance(reviews, dict):
        return errors + ["reviews must be an object keyed by repository path"]
    allowed, exemptions = eligible(contract), exemption_map(contract)
    for path, review in reviews.items():
        if path not in allowed:
            kind = (
                "exempt artifacts must not carry review receipts"
                if path in exemptions
                else "review is outside the declared clarity scope"
            )
            errors.append(f"{path}: {kind}")
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
    errors, exemptions = scope_errors(contract), exemption_map(contract)
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
    defects = errors + [
        f"{path}: clarity candidate is not assigned to a campaign"
        for path in grouped["_unassigned"]
    ]
    if defects:
        print("\nScope errors")
        for defect in defects:
            print(f"ERROR: {defect}")
        return 1
    print("\nPASS: every current prose candidate is eligible or explicitly exempt")
    return 0

def do_next(contract: dict, record: dict) -> int:
    states, grouped = state_map(contract, record), campaigns(contract)
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
    contract: dict, record: dict, path_text: str,
    basis_args: list[str] | None, changed: bool,
) -> int:
    artifact = (ROOT / path_text).resolve()
    try:
        path = artifact.relative_to(ROOT).as_posix()
    except ValueError:
        raise SystemExit("path must stay inside the repository")
    if path in exemption_map(contract):
        raise SystemExit(f"{path} is explicitly exempt from clarity review")
    if path not in eligible(contract) or not artifact.is_file():
        raise SystemExit(f"{path} is outside the declared clarity scope or missing")
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

def do_check(contract: dict, record: dict) -> int:
    errors = registry_errors(contract, record)
    stale = [
        f"{path}: {state}"
        for path, state in state_map(contract, record).items()
        if state in {"TEXT_STALE", "BASIS_STALE"}
    ]
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
    incomplete = [
        f"{path}: {state}"
        for path, state in state_map(contract, record).items()
        if state not in {"CURRENT", "EXEMPT"}
    ]
    for item in incomplete:
        print(f"INCOMPLETE: {item}")
    if incomplete:
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
