#!/usr/bin/env python3
"""Refuse a standing claim that no witness record supports.

`AGENTS.md` fixes the lifecycle `OPEN -> BUILT -> WITNESSED -> RATIFIED` and
states that a build report cannot witness itself. That rule has been in the
repository the whole time, and on 2026-08-23 a session read it and then spent a
day asking the owner to ratify work that had never been witnessed. The rule was
never the problem. Nothing made it fire.

This makes it fire. A `*_status` field in `STATUS.yaml` may not claim
`WITNESSED` or `RATIFIED` standing unless a witness record exists naming that
subject. Claiming the standing and writing the record are then the same act.

Scope, stated so it is not mistaken for more: this checks standing FIELDS in
`STATUS.yaml`. It does not police open-decision removal, and it cannot tell a
good witness record from a bad one - it checks that an independent record was
deposited, not that it was persuasive. Only Bdo ratifies; this refuses a claim
that was never witnessed at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
STATUS = ROOT / "STATUS.yaml"
WITNESS_DIR = ROOT / "witness"

CLAIMS = ("WITNESSED", "RATIFIED")
FIELD = re.compile(r"^([a-z0-9_]+_status):\s*(\S+)\s*$")


@dataclass(frozen=True)
class Claim:
    """A standing a status field asserts about its subject."""

    field: str
    subject: str
    value: str
    standing: str


def claimed_standing(value: str) -> str | None:
    """The standing a status value asserts, or None if it asserts none.

    Negation matters more than it looks. `BUILT_SELF_TESTED_NOT_WITNESSED`
    contains the token `WITNESSED` and asserts the exact opposite; a substring
    match reports every unwitnessed subject in the repository as witnessed.
    Tokens are compared whole, and a token preceded by `NOT` is a denial.
    """
    tokens = value.upper().split("_")
    for index, token in enumerate(tokens):
        if token not in CLAIMS:
            continue
        if index > 0 and tokens[index - 1] == "NOT":
            continue
        return token
    return None


def subject_of(field: str) -> str:
    """The subject a status field is about: `asset_service_status` -> `asset-service`."""
    stem = field[: -len("_status")] if field.endswith("_status") else field
    return stem.replace("_", "-")


def read_claims(status_path: Path = STATUS) -> list[Claim]:
    """Every standing claim asserted by a status field."""
    if not status_path.is_file():
        return []
    claims = []
    for line in status_path.read_text(encoding="utf-8", errors="replace").split("\n"):
        match = FIELD.match(line)
        if not match:
            continue
        field, value = match.group(1), match.group(2)
        standing = claimed_standing(value)
        if standing is not None:
            claims.append(Claim(field=field, subject=subject_of(field), value=value, standing=standing))
    return claims


def witness_records(witness_dir: Path = WITNESS_DIR) -> set[str]:
    """Subjects that carry a witness record, by filename stem."""
    if not witness_dir.is_dir():
        return set()
    return {p.stem.lower() for p in witness_dir.glob("*.md")}


def unsupported(status_path: Path = STATUS, witness_dir: Path = WITNESS_DIR) -> list[Claim]:
    """Standing claims with no witness record naming their subject."""
    records = witness_records(witness_dir)
    return [c for c in read_claims(status_path) if c.subject.lower() not in records]


def main(argv: list[str] | None = None) -> int:
    claims = read_claims()
    records = witness_records()
    gaps = unsupported()

    for claim in claims:
        mark = "REFUSED" if claim in gaps else "SUPPORTED"
        print(f"{mark:<10} {claim.field} claims {claim.standing}")
        if claim in gaps:
            print(f"           no witness record at witness/{claim.subject}.md", file=sys.stderr)

    if gaps:
        print(
            f"\nFAIL: {len(gaps)} standing claim(s) no witness record supports.\n"
            "AGENTS.md fixes OPEN -> BUILT -> WITNESSED -> RATIFIED, and a build report\n"
            "cannot witness itself. Deposit an independent observation under witness/\n"
            "naming the subject, or lower the claim back to what the evidence carries.",
            file=sys.stderr,
        )
        return 1

    if not claims:
        print(f"PASS: no status field claims WITNESSED or RATIFIED ({len(records)} record(s) on file)")
        print("Standing note: nothing here has been witnessed, and the check says so rather than staying silent.")
        return 0

    print(f"\nPASS: {len(claims)} standing claim(s), each with a witness record")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
