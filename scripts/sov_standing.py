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

# The field is read from a declared position, never searched for in the document.
#
# The previous repair stripped fenced blocks, inline spans and HTML comments and
# then searched what remained. A fourth reading walked four quotation forms past
# it: a nested four-backtick fence, an unterminated fence, a blockquoted label,
# and an indented one. That was the correct finding and the general one - there
# is no finite list of ways markdown can quote, so stripping what looks like
# quotation is enumeration wearing structure's clothes. It is the same mistake
# the value half of this gate had already been repaired for, made again on the
# other axis in the same commit.
#
# A position has no such tail. The block must be the first content in the file,
# after an optional heading, and nothing after it is read at all. A record may
# then quote anything, in any nesting, terminated or not, without touching what
# it declares - which matters, because the most likely record to quote this gate
# is a record about this gate.
BLOCK_OPEN = "```witness"
BLOCK_CLOSE = "```"
STANDING_FIELD = "standing_supported"

# The whole value must BE a standing. Scanning a value for one is what three
# readings each defeated in a new way: `SELF_WITNESSED` splits into SELF and
# WITNESSED under any tokeniser, so a scan reads a self-witness - the one
# inversion `AGENTS.md` exists to forbid - as support for it. `PRE-WITNESSED`,
# `WITNESSED subject to conditions` and `WITNESSED (retracted)` each defeated a
# different hand-written denial list, and such a list has no end. Inside a plain
# text block there is no emphasis to strip either, so `WITNESSED*` and its
# footnote are simply not this word.
SUPPORTED_VALUES = {"WITNESSED": "WITNESSED", "RATIFIED": "RATIFIED"}


def declared_block(text: str) -> list[str] | None:
    """The record's declaration block, or None if it does not open with one.

    Position is the whole point. The block is the first content in the file, past
    blank lines and an optional heading; anything else there means the record
    declares nothing. An unterminated block is not a block.
    """
    lines = text.split("\n")
    index = 0
    while index < len(lines) and (not lines[index].strip() or lines[index].startswith("#")):
        index += 1
    if index >= len(lines) or lines[index].strip() != BLOCK_OPEN:
        return None
    index += 1
    body: list[str] = []
    while index < len(lines) and lines[index].strip() != BLOCK_CLOSE:
        body.append(lines[index])
        index += 1
    return body if index < len(lines) else None


def declared_field(text: str) -> str | None:
    """The one `standing_supported` value the record's own block states.

    Stated twice is stated ambiguously and counts as not stated: a record says
    this once or it says nothing.
    """
    body = declared_block(text)
    if body is None:
        return None
    found = [line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else ""
             for line in body if line.split(None, 1)[:1] == [STANDING_FIELD]]
    return found[0] if len(found) == 1 else None


def supported_standing(record: Path) -> str | None:
    """The standing this record declares, or None if it declares none.

    A filename is a declaration; what the record says is the artifact. This reads
    one field from one declared position and compares its whole value against a
    closed set. It does not read English and does not search the document.

    Non-ASCII is refused before the comparison. Case folding is not identity -
    the Turkish dotless i upper-cases to `I`, so a lookalike spelling would walk
    straight through an exact match.
    """
    try:
        text = record.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    value = declared_field(text)
    if value is None:
        return None
    value = value.strip()
    if not value.isascii():
        return None
    return SUPPORTED_VALUES.get(value.upper())


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
                " `Standing supported:` line must read exactly WITNESSED, once, on"
                " the label's own line and outside any quoted block")
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
