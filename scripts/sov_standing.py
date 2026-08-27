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


NOT_A_RECORD = {"readme", "index"}

# A witness record carries a subject at most to WITNESSED. `AGENTS.md` reserves
# ratification for a seat that settles JUDGEMENT, and `witness/README.md` says
# the same: depositing a record makes advancing standing possible and never
# performs it. A record declaring RATIFIED has over-reached, and the gate names
# that rather than quietly declining to count it.
WITNESS_MAY_SUPPORT = "WITNESSED"

# The label, and the rest of its own line. The value must sit on the label line:
# `**Standing supported:**` with the verdict on the line below once captured the
# literal `**`, which is not `none` and so read as support. The line break is a
# boundary here rather than something to search past.
LABEL = re.compile(r"^[^A-Za-z0-9\n]*standing\s+supported[^A-Za-z0-9\n]*(.*)$",
                   re.IGNORECASE | re.MULTILINE)

# Any of these anywhere in the value denies it. `NOT_WITNESSED` is why the
# discipline exists at all, but `RATIFIED is refused` and `no standing supported`
# deny just as plainly while a preceding-token rule misses both.
DENIALS = frozenset({
    "NOT", "NO", "NONE", "NOTHING", "NEVER", "WITHOUT", "CANNOT", "PENDING",
    "REFUSED", "REFUSES", "DENIED", "DENIES", "DECLINED", "DECLINES",
    "WITHHELD", "UNSUPPORTED", "INSUFFICIENT",
})


def supported_standing(record: Path) -> str | None:
    """The standing this record's own text declares, or None if it declares none.

    A filename is a declaration; what the record says is the artifact. This reads
    a narrow machine-readable field and deliberately does not read English: the
    value must name exactly one of `WITNESSED` or `RATIFIED` and carry no denial.
    Silence, prose, ambiguity, `n/a`, and `OPEN -> BUILT` all support nothing,
    because a gate that infers a verdict from a sentence is a gate that can be
    written past by anyone writing an ordinary sentence.
    """
    try:
        text = record.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    found = LABEL.search(text)
    if found is None:
        return None
    tokens = [token.upper() for token in re.split(r"[^A-Za-z]+", found.group(1)) if token]
    named = {token for token in tokens if token in CLAIMS}
    if len(named) != 1 or any(token in DENIALS for token in tokens):
        return None
    return named.pop()


def witness_records(witness_dir: Path = WITNESS_DIR) -> dict[str, str]:
    """Subject to the standing its record declares, for records that declare one.

    The directory's own documentation is not an observation of anything. Counting
    it would let the file that explains the convention satisfy a claim made under
    that convention.
    """
    if not witness_dir.is_dir():
        return {}
    declared = {}
    for path in sorted(witness_dir.glob("*.md")):
        stem = path.stem.lower()
        if stem in NOT_A_RECORD:
            continue
        standing = supported_standing(path)
        if standing is not None:
            declared[stem] = standing
    return declared


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
                " `Standing supported:` line must name WITNESSED on the label's own"
                " line and carry no denial")
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
