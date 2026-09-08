#!/usr/bin/env python3
"""Grade what the Communications seat asserts against the records owning it.

The Communications seat is the only participant that speaks to a person, and it
was the only claim surface in this repository with no grader. Every rule it
carries was an instruction, and nothing failed when one was broken: two agent
definitions asserted a breakdown of 379 of the owner's turns for weeks, against
no transcript corpus and no command producing any part of it, and the surface
that repeats a claim to every launched participant is exactly the one where an
ungraded claim does the most work.

What this reaches and what it does not is declared in
`contracts/comms-claims.json`. Three kinds run here. `UNSOURCED_NUMBER` asks a
paragraph carrying a behavioural figure to name what produces it.
`INTERNAL_TOKEN` refuses machine vocabulary in a message addressed to a person.
`UNSUPPORTED_STANDING` grades a witnessed or ratified claim against
`scripts/sov_standing.py`, which reads STATUS.yaml and the witness records by
paths this module does not touch.

This does not grade whether prose is clear, whether it answered the question, or
whether it is too long. No oracle exists for any of the three, a phrasing list
would be a declared case pretending to be a net, and a global brevity rule was
measured as harmful upstream and withdrawn. What is enforceable here is truth,
not style, and the contract's `not_covered` says so rather than leaving the
silence to be read as coverage.

Usage:
    python scripts/sov_comms.py                 grade the declared surfaces
    python scripts/sov_comms.py check <path|->  grade one drafted message
    python scripts/sov_comms.py selfcheck       prove every refusal fires
"""

from __future__ import annotations

from pathlib import Path
import json
import sys

from sovcomms.kinds import (Defect, check_internal_token, check_unsourced_number,
                            check_unsupported_standing, supported_standing)

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "contracts" / "comms-claims.json"


def contract() -> dict:
    """The coverage declaration, read from bytes at the moment it is needed."""
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def grade_surfaces(root: Path = ROOT) -> list[Defect]:
    """Grade every agent definition the contract names as a Communications surface."""
    spec = contract()
    declared = spec["subjects"]["surfaces"]
    historical = frozenset(spec.get("historical_claims", {}))
    supported = supported_standing(root)
    defects: list[Defect] = []
    for relative in declared:
        path = root / relative
        if not path.exists():
            defects.append(Defect("DEAD_SURFACE", relative,
                                  "declared in contracts/comms-claims.json and absent"))
            continue
        text = path.read_text(encoding="utf-8")
        defects.extend(check_unsourced_number(relative, text, historical))
        defects.extend(check_unsupported_standing(relative, text, supported))
    return defects


def grade_message(where: str, text: str, root: Path = ROOT) -> list[Defect]:
    """Grade one drafted message: every kind applies, internal vocabulary included."""
    return (check_unsourced_number(where, text)
            + check_internal_token(where, text)
            + check_unsupported_standing(where, text, supported_standing(root)))


def selfcheck() -> list[str]:
    """Prove each declared refusal fires, and that clean text is not refused.

    The cases are carried here rather than read from the tree, so repairing the
    live surfaces cannot stop a refusal being proved. A grader that cannot refuse
    passes every repository silently.
    """
    failures: list[str] = []
    cases = [
        ("UNSOURCED_NUMBER",
         "Measured against 379 of his turns: five were genuine owner rulings.",
         check_unsourced_number),
        ("UNSOURCED_NUMBER",
         "Across 68 measured sessions, 72% of all tool calls were reading.",
         check_unsourced_number),
        ("INTERNAL_TOKEN",
         "The asset slice is WITNESSED and the rest is UNATTESTABLE.",
         check_internal_token),
        ("UNSUPPORTED_STANDING",
         "proofing_service_status is WITNESSED as of this run.",
         lambda where, text: check_unsupported_standing(where, text, set())),
    ]
    for kind, text, fn in cases:
        found = fn("selfcheck", text)
        if not any(d.kind == kind for d in found):
            failures.append(f"{kind}: no refusal fired for {text!r}")

    clean = [
        "102 commits sat on branches that never reached the trunk.\n"
        "Before you finish, run `python scripts/sov_strand.py`.",
        "Its budget is 60 agent invocations per exercise and it expires 2026-11-23.",
        "Two of the six exit clauses are done and the rest are not.",
    ]
    for text in clean:
        found = check_unsourced_number("selfcheck", text) + check_internal_token(
            "selfcheck", text)
        if found:
            failures.append(f"clean text refused: {text!r} -> {[d.kind for d in found]}")

    denial = check_unsupported_standing(
        "selfcheck", "observation_service_status is NOT_WITNESSED", set())
    if denial:
        failures.append("NOT_WITNESSED read as a claim; trap T3 not honoured")

    # An exemption that clears its whole surface is worse than none: it hides
    # every later claim behind one recorded sentence.
    mixed = ('A rule once quoted "379 of his turns" and still does.\n\n'
             "Across 68 measured sessions the pattern held.")
    if not check_unsourced_number("selfcheck", mixed, frozenset({"379 of his turns"})):
        failures.append("a recorded historical sentence cleared the whole surface")

    declared = set(contract()["refusals"])
    proved = {kind for kind, _, _ in cases}
    if declared - proved:
        failures.append(f"declared refusals no case fires: {sorted(declared - proved)}")
    return failures


def main(argv: list[str]) -> int:
    """Grade the surfaces, one message, or the refusals themselves."""
    mode = argv[1] if len(argv) > 1 else "grade"

    if mode == "selfcheck":
        failures = selfcheck()
        for line in failures:
            print(f"FAIL: {line}")
        if failures:
            return 1
        print("PASS: every declared Communications refusal fires, and clean text is not")
        return 0

    if mode == "check":
        if len(argv) < 3:
            print("usage: sov_comms.py check <path|->", file=sys.stderr)
            return 2
        target = argv[2]
        text = sys.stdin.read() if target == "-" else Path(target).read_text(encoding="utf-8")
        defects = grade_message("message" if target == "-" else target, text)
    elif mode == "grade":
        defects = grade_surfaces()
    else:
        print(f"unknown mode {mode!r}", file=sys.stderr)
        return 2

    for defect in defects:
        print(defect)
    if defects:
        print(f"\nFAIL: {len(defects)} Communications claim(s) the record does not support. "
              f"Coverage and its limits are in contracts/comms-claims.json.")
        return 1
    print("PASS: no unsourced figure, machine token or unsupported standing claim")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
