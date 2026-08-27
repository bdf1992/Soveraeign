"""Reconcile what the router sends to Bdo against what the policy permits to reach him.

Two contracts describe the same gate and have never met.

`contracts/acceptance-policy.json` lists seven hold reasons and says of them: "This
list is exhaustive. A transition may wait on the owner only for a reason named here.
Wanting the owner's opinion is not a reason."

`contracts/acceptance-routing.json` routes on `categories`, whose values today are
`product_intent`, `acceptance_standing` and `external_commitment`. Not one of the
three is a hold reason. So a question can be routed to Bdo without anything ever
asking whether the policy admits it, and 29 currently are.

`decisions/0046` drained seventeen questions to roughly two on 2026-08-25. Four days
later the count was seventeen again. Draining is an act; nothing here was a check, so
the queue regrew exactly as fast as records were minted.

A question passes by naming a `hold_reason` from the policy's list. The gap is
reported as debt and never as a defect: closing it means deciding whether
`product_intent` is admissible at all, which would strike most of the queue at once.
That is a governing choice, and a reader may not make it by failing a build.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "contracts" / "acceptance-policy.json"
ROUTING = ROOT / "contracts" / "acceptance-routing.json"
NL = chr(10)


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def gap() -> tuple[list[dict[str, Any]], set[str], int]:
    """Return the owner-routed questions citing no admissible reason, and the totals."""
    reasons = set(_read(POLICY)["hold_reasons"])
    routed = _read(ROUTING)["questions"]
    owner_routed = 0
    gaps: list[dict[str, Any]] = []
    for qid, entry in sorted(routed.items()):
        if not entry.get("reaches_owner"):
            continue
        owner_routed += 1
        declared = entry.get("hold_reason")
        named = {declared} if isinstance(declared, str) else set(declared or [])
        if not named & reasons:
            gaps.append({"id": qid, "categories": entry.get("categories") or [],
                         "question": entry.get("question", "")})
    return gaps, reasons, owner_routed


def render() -> str:
    """Render the reconciliation as a table a person can act on."""
    gaps, reasons, owner_routed = gap()
    lines = ["Admissible hold reasons (contracts/acceptance-policy.json, declared "
             "exhaustive):"]
    lines.extend(f"  {reason}" for reason in sorted(reasons))
    lines.append("")
    lines.append(f"{owner_routed} question(s) route to Bdo. {len(gaps)} name no admissible "
                 "hold reason:")
    for entry in gaps:
        lines.append(f"  {entry['id']:<10} {entry['question'][:46]:<48}"
                     + ",".join(entry["categories"]))
    lines.append("")
    lines.append("A category is not a hold reason. Until a question declares one, nothing has "
                 "checked that the policy permits it to wait on him.")
    return NL.join(lines)


def debt_line() -> str:
    """One line for the gate, or empty when every routed question names a reason."""
    gaps, reasons, _ = gap()
    if not gaps:
        return ""
    return (f"DEBT: {len(gaps)} owner-routed question(s) name no hold reason from the "
            f"{len(reasons)} in contracts/acceptance-policy.json, which declares its list "
            "exhaustive. The router routes on categories and the policy admits reasons, and "
            "the two vocabularies do not intersect. "
            "`python scripts/sov_docket.py holds` lists them.")
