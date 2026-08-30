#!/usr/bin/env python3
"""Read the standing authority grants, and grade one request against them.

`SPEC.md` declares the `AuthorityGrant` object and requires an authority check
at every consequential transition. This is the reader and the command line for
that check. It settles nothing and performs nothing: `check` returns a verdict,
and whatever the verdict permits is done by the caller.

`list` prints the issued grants and whether each is presently live. `check`
grades one request file. `selfcheck` grades the declared corpus in
`conformance/fixtures/authority/grant-cases.json` and validates every issued
grant against the schema, so a grant that could never be evaluated cannot sit in
the registry looking authoritative.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovkernel import authority  # noqa: E402
from sovkernel import jsonschema  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts" / "authority-grant.schema.json"
REGISTRY = ROOT / "contracts" / "standing-grants.json"
CORPUS = ROOT / "conformance" / "fixtures" / "authority" / "grant-cases.json"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_grants(path: Path = REGISTRY) -> list[dict]:
    """Read the issued standing grants in registry order."""
    return _read(path)["grants"]


def _merge(base: dict, patch: dict) -> dict:
    """Apply a corpus patch over a base, replacing whole sub-objects by key.

    A nested dict is merged one level deeper so a case can change `scope.branches`
    without restating the paths; anything else the patch names replaces the base
    value outright.
    """
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


def cmd_list(_args: argparse.Namespace) -> int:
    """Print every issued grant and whether it is live right now."""
    now = datetime.now(timezone.utc).isoformat()
    grants = load_grants()
    probe = {"actor_id": None, "capability": None, "effect_class": "RECORD_LOCAL", "at": now}
    for grant in grants:
        reason = authority._grant_unavailable(grant, probe, authority._instant(now, "at"))
        # The probe carries no actor and no capability, so the first two reasons are
        # always about the probe rather than the grant. Anything past them is real.
        stale = reason if reason and "actor" not in reason and "capability" not in reason else None
        state = f"NOT LIVE: {stale}" if stale else f"live ({grant['status']})"
        print(f"{grant['grant_id']}  {grant['authority_type']:<12} {state}")
        print(f"  issuer {grant['issuer_id']} -> actor {grant['actor_id']}")
        print(f"  capabilities: {', '.join(grant['capabilities'])}")
        print(f"  ceiling {grant['effect_ceiling']}, budget "
              f"{grant['budget']['ceiling']} {grant['budget']['unit']}, "
              f"until {grant['valid_until']}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Grade one request file against the issued grants."""
    request = _read(Path(args.request))
    result = authority.evaluate(load_grants(), request)
    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['verdict']}: {result['code'] or result['grant_id']}")
        print(f"  {result['detail']}")
    return 0 if result["verdict"] == authority.PERMITTED else 1


def _schema_failures() -> list[str]:
    """Every issued grant must validate against the declared schema."""
    schema = _read(SCHEMA)
    failures = []
    for grant in load_grants():
        for error in jsonschema.validate(grant, schema, schema):
            failures.append(f"{grant.get('grant_id')}: {error}")
    return failures


def _corpus_failures() -> tuple[list[str], int]:
    """Grade the declared corpus; return failures and the number of cases run."""
    corpus = _read(CORPUS)
    base_grant = corpus["base_grant"]
    base_request = corpus["base_request"]
    failures = []
    for case in corpus["cases"]:
        grant = _merge(base_grant, case.get("grant_patch") or {})
        request = _merge(base_request, case.get("request_patch") or {})
        result = authority.evaluate([grant], request)
        expected = case["expect"]
        actual = result["code"] if result["verdict"] == authority.REFUSED else "PERMITTED"
        if actual != expected:
            failures.append(f"{case['case_id']}: expected {expected}, got {actual} "
                            f"({result['detail']})")
    return failures, len(corpus["cases"])


def _uncovered_codes() -> list[str]:
    """Every refusal code the evaluator can report needs a case proving it fires."""
    corpus = _read(CORPUS)
    expected = {case["expect"] for case in corpus["cases"]}
    reportable = {authority.AUTHORITY_REFUSED, authority.MISSING_PRECONDITION,
                  authority.OBSERVATION_MISSING, authority.OBSERVER_NOT_INDEPENDENT}
    return sorted(reportable - expected)


def cmd_selfcheck(_args: argparse.Namespace) -> int:
    """Validate the registry against the schema and grade the declared corpus."""
    failures = [f"schema: {f}" for f in _schema_failures()]
    corpus_failures, case_count = _corpus_failures()
    failures.extend(f"corpus: {f}" for f in corpus_failures)
    failures.extend(f"corpus: no case proves {code} fires" for code in _uncovered_codes())
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        return 1
    print(f"PASS: {len(load_grants())} grant(s) valid, {case_count} authority cases graded")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="print issued grants and whether each is live")

    check = sub.add_parser("check", help="grade one request file against the grants")
    check.add_argument("request", help="path to a request JSON file")
    check.add_argument("--json", action="store_true", dest="as_json",
                       help="emit machine-readable output")

    sub.add_parser("selfcheck", help="validate the registry and grade the declared corpus")

    args = parser.parse_args(argv)
    return {"list": cmd_list, "check": cmd_check, "selfcheck": cmd_selfcheck}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
