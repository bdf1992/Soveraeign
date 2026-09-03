#!/usr/bin/env python3
"""Materialise the grant-cases.json corpus into concrete grants and requests.

Stdlib only. For each case in `conformance/fixtures/authority/grant-cases.json`,
apply its `grant_patch` and `request_patch` over `base_grant`/`base_request` using
the same `_merge` function `scripts/sov_grant.py` uses for its own selfcheck, call
`sovkernel.authority.evaluate`, and record the evaluator's actual verdict beside
the case's declared expectation.

This module reads `scripts/sov_grant.py` and `scripts/sovkernel/*` and writes only
`cases.materialised.json` under this experiment directory. It is not imported by
anything under `scripts/`, `services/`, `conformance/`, or `bindings/`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
CORPUS = ROOT / "conformance" / "fixtures" / "authority" / "grant-cases.json"
OUT = Path(__file__).resolve().parent / "cases.materialised.json"

sys.path.insert(0, str(SCRIPTS))

from sov_grant import _merge  # noqa: E402
from sovkernel import authority  # noqa: E402
from sovkernel import scope as scope_mod  # noqa: E402

OUTSIDE_CODES = {
    authority.OBSERVATION_MISSING,
    authority.OBSERVER_NOT_INDEPENDENT,
    authority.MISSING_PRECONDITION,
}


def tier(case: dict) -> tuple[str, bool]:
    """Tier from the case's expected code and its patched fields alone.

    `OUTSIDE` covers the preconditions the kernel checks after a grant already
    covers the request - they are not an authority decision. Any case whose
    `request_patch` touches `paths` is a `SCOPE` case: scope is the only thing a
    path patch can be exercising, and no `CEDAR`-tier case patches `paths`.
    Everything else is `CEDAR`: status, actor, capability, issuer, revocation,
    the time window, the effect ceiling, branch, and budget.

    A `SCOPE` case is tagged `precomputed=True` when at least one of its patched
    paths is one `sovkernel.scope._ungradeable` refuses outright - a wildcard, a
    non-naming segment, a backslash, pathspec magic, or an absolute path. None of
    those escapes has a segment Cedar's entity hierarchy can represent, so a
    project step 5 case built for one gives Cedar an unresolved `Path` entity
    rather than the real string.
    """
    expect = case["expect"]
    if expect in OUTSIDE_CODES:
        return "OUTSIDE", False
    request_patch = case.get("request_patch") or {}
    paths = request_patch.get("paths")
    if paths is None:
        return "CEDAR", False
    precomputed = any(scope_mod._ungradeable(p) is not None for p in paths)
    return "SCOPE", precomputed


def main() -> int:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    base_grant = corpus["base_grant"]
    base_request = corpus["base_request"]
    materialised = []
    for case in corpus["cases"]:
        grant = _merge(base_grant, case.get("grant_patch") or {})
        request = _merge(base_request, case.get("request_patch") or {})
        result = authority.evaluate([grant], request)
        actual_code = None if result["verdict"] == authority.PERMITTED else result["code"]
        actual_verdict = "PERMITTED" if result["verdict"] == authority.PERMITTED else result["code"]
        case_tier, precomputed = tier(case)
        materialised.append({
            "case_id": case["case_id"],
            "tier": case_tier,
            "precomputed": precomputed,
            "grant": grant,
            "request": request,
            "expected": case["expect"],
            "kernel_verdict": actual_verdict,
            "kernel_code": actual_code,
            "kernel_grant_id": result["grant_id"],
            "kernel_detail": result["detail"],
            "kernel_considered": result["considered"],
        })

    tiers = {}
    for m in materialised:
        tiers[m["tier"]] = tiers.get(m["tier"], 0) + 1
    precomputed_count = sum(1 for m in materialised if m["precomputed"])

    OUT.write_text(json.dumps({
        "corpus_id": corpus["corpus_id"],
        "case_count": len(materialised),
        "tier_counts": tiers,
        "scope_precomputed_count": precomputed_count,
        "cases": materialised,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    mismatches = [m["case_id"] for m in materialised if m["kernel_verdict"] != m["expected"]]
    print(f"materialised {len(materialised)} cases -> {OUT}")
    print(f"tiers: {tiers}; scope precomputed: {precomputed_count}")
    if mismatches:
        print(f"WARNING: kernel verdict disagrees with the corpus's own expectation for: {mismatches}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
