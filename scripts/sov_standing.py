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
good witness record from a bad one - it reads the one machine-readable field a
record must carry, `Standing supported:`, and grades that. Whether the record
attacked the subject honestly is a reader's judgement, and whether the record is
about the subject at all rests on its filename, which is a convention and not a
proof. Only Bdo ratifies; this refuses a claim no record supports.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovstanding import records  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STATUS = ROOT / "STATUS.yaml"

# Re-exported so a caller and every existing case keep one entry point, while
# the two readings live in separate modules.
WITNESS_DIR = records.WITNESS_DIR
NOT_A_RECORD = records.NOT_A_RECORD
WITNESS_MAY_SUPPORT = records.WITNESS_MAY_SUPPORT
MAX_BLOCK_LINES = records.MAX_BLOCK_LINES
SUPPORTED_VALUES = records.SUPPORTED_VALUES
declared_block = records.declared_block
declared_field = records.declared_field
supported_standing = records.supported_standing
witness_records = records.witness_records

CLAIMS = ("WITNESSED", "RATIFIED")
FIELD = re.compile(r"^\s*([a-z0-9_]+_status):\s*(.+?)\s*$")

# A trailing YAML comment and a quoted value are what an ordinary edit to
# STATUS.yaml produces, and both hid a claim entirely: the value never reached
# the token compare. Indented fields were invisible for the same reason, and
# the live file carries 22 nested mappings. Liberal is the safe direction on
# this side - over-reading asks for a witness record that may not be needed,
# under-reading lets a claim through unasked.
COMMENT_TAIL = re.compile(r"\s+#.*$")


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


def bare_value(value: str) -> str:
    """A status value with YAML decoration removed, before it is read as a claim.

    `WITNESSED  # see witness/asset-service.md` and `"WITNESSED"` are both the
    file's own idiom and both hid the claim completely.
    """
    return COMMENT_TAIL.sub("", value).strip().strip("\"'").strip()


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
        standing = claimed_standing(bare_value(value))
        if standing is not None:
            claims.append(Claim(field=field, subject=subject_of(field), value=value, standing=standing))
    return claims


def refusal(claim: Claim, witness_dir: Path = WITNESS_DIR) -> str | None:
    """Why this claim is refused, in the record's own terms, or None if supported.

    Both `WITNESSED` and `RATIFIED` claims need the same thing here, because
    nothing is ratified that was not first witnessed. What this gate cannot see
    is the owner half of a ratification, and it says so rather than implying a
    passing RATIFIED claim was checked end to end.
    """
    subject = claim.subject.lower()
    path = witness_dir / f"{subject}.md"
    if subject in NOT_A_RECORD or not path.is_file():
        return f"no witness record at witness/{claim.subject}.md"
    declared = supported_standing(path)
    if declared is None:
        return (f"witness/{claim.subject}.md names no standing it supports; the"
                " record must open with a ```witness block holding"
                " `standing_supported  WITNESSED` and nothing but field lines")
    if declared != WITNESS_MAY_SUPPORT:
        return (f"witness/{claim.subject}.md declares {declared}, which no witness"
                " record may support; a record carries a subject to WITNESSED and"
                " the owner settles the rest")
    return None


def unsupported(status_path: Path = STATUS, witness_dir: Path = WITNESS_DIR) -> list[Claim]:
    """Standing claims that no witness record supports."""
    return [c for c in read_claims(status_path) if refusal(c, witness_dir) is not None]


def main(argv: list[str] | None = None) -> int:
    claims = read_claims()
    records = witness_records()
    reasons = {claim.field: refusal(claim) for claim in claims}
    gaps = [claim for claim in claims if reasons[claim.field] is not None]

    for claim in claims:
        refused = reasons[claim.field]
        print(f"{'REFUSED' if refused else 'SUPPORTED':<10} {claim.field} claims {claim.standing}")
        if refused:
            print(f"           {refused}", file=sys.stderr)
        elif claim.standing == "RATIFIED":
            print("           witnessed half only; this gate does not see the owner's act")

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
