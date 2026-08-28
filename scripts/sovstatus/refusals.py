"""The refusals a status-claim crosswalk entry can earn, and the derivations behind them.

Kept apart from `scripts/sov_status_claims.py` so the table can grow without dragging the
reader and the command line past the module budget with it. The reader owns what counts as
a status field; this owns what counts as a wrong entry.

Nothing an entry declares is trusted where it can be derived, and nothing is derived from
prose. The subject is the field stem. The claim kind is fixed by the value's own leading
tokens. The set of keys an entry may carry is closed.

This table used to extract an artifact standing from the value, and three independent
witnesses broke three attempts at it. The first read a standing from prose and admitted
`WITNESSED` on a value reading `NOT_WITNESSED`. The second compared whole tokens and treated
`NOT` as denial, and fell to `NOT_YET`, `NEVER`, `AWAITING`, and to `BUILT-NOT_WITNESSED`,
where a hyphen hid the negator. The third asked only what the value led with, and fell to
`WITNESSED_RETRACTED`, `RATIFIED_NOT` and `-WITNESSED`, where splitting on non-alphanumerics
deletes a negator rather than seeing it. Each draft closed the instance it was shown and left
the class open in a new spelling.

The fourth answer is not a fourth spelling. The extraction is gone. Whether something is
witnessed is a standing claim, `scripts/sov_standing.py` already owns it and checks the thing
that decides it - whether a witness record exists naming the subject - and a second, weaker
standing rule here was the competing authority `AGENTS.md` forbids. Reading a structured fact
out of unstructured prose is what kept failing; not doing it is the repair.

What this table owns is which subject a status line is about and which kind of claim it
makes. No witness has broken that across three rounds.
"""

from __future__ import annotations

import re

PACKET_TOKEN = re.compile(r"\AA(\d+)\Z")
PACKET_REFERENCE = re.compile(r"\AA(\d+)\Z")
SEPARATORS = re.compile(r"[^A-Za-z0-9]+")
SUFFIX = "_status"
SHAPE = {"field": str, "value": str, "subject": str, "claim_kind": str, "detail": str}
# Closed. A witness added asserted_standing, settled_by, authority and a resurrected
# standing_source to a live entry and every one passed: a type check over named keys
# never rejects an unnamed one.
KEYS = frozenset(SHAPE) | {"reference"}


def tokens(value: str) -> list[str]:
    """The value's tokens, upper-cased, split on every non-alphanumeric run.

    Splitting on underscores alone let `BUILT-NOT_WITNESSED` read as two tokens, so a
    negator written with a hyphen was never seen by a rule looking for one.
    """
    return [token for token in SEPARATORS.split(value.upper()) if token]


def derived_subject(field: str) -> str:
    """The only subject a field admits: its stem, with underscores hyphenated."""
    return field[: -len(SUFFIX)].replace("_", "-") if field.endswith(SUFFIX) else field


def expected_kind(value: str) -> str:
    """The only claim kind a value's own prefix admits. Total over every value.

    `OWNER_ACCEPTED_A<digit>` is the packet convention `STATUS.yaml` states in its own
    comment: it "names the packet the root seat acted on". A bare `OWNER_ACCEPTED_...`
    value is the document reporting that an acceptance happened, which is a status about
    an act rather than the record of the act. Eighteen live fields turn on that reading and
    it is Bdo's to overturn; see `decisions/0074`, Residuals.
    """
    found = tokens(value)
    if found[:1] == ["RULED"]:
        return "RULING"
    if found[:2] == ["OWNER", "ACCEPTED"] and len(found) > 2 and PACKET_TOKEN.match(found[2]):
        return "OWNER_ACCEPTANCE"
    return "STATUS"


def malformed(_f: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    """ENTRY_MALFORMED - an entry that would otherwise raise instead of refusing."""
    defects = []
    for index, entry in enumerate(entries):
        bad = [k for k, kind in SHAPE.items() if not isinstance(entry.get(k), kind)]
        if bad:
            defects.append(f"ENTRY_MALFORMED: entry {index} lacks well-formed {', '.join(bad)}")
        elif "reference" not in entry:
            defects.append(f"ENTRY_MALFORMED: entry {index} ({entry['field']}) omits a "
                           "reference")
    return defects


def unknown_key(_f: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    """ENTRY_UNKNOWN_KEY - an entry may carry no key this table does not grade.

    The set is closed rather than merely type-checked. A witness put `asserted_standing`,
    `settled_by`, `authority` and a resurrected `standing_source` onto live entries and every
    one passed, because checking the types of named keys never rejects an unnamed one.
    """
    return [f"ENTRY_UNKNOWN_KEY: {e.get('field')} carries {sorted(set(e) - KEYS)}, which this "
            "table does not grade"
            for e in entries if set(e) - KEYS]


def untyped(fields: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    """FIELD_UNTYPED - the document says something the crosswalk does not read."""
    declared = {(e.get("field"), e.get("value")) for e in entries}
    return [f"FIELD_UNTYPED: STATUS.yaml carries {f}: {v} and the crosswalk does not type it"
            for f, v in fields if (f, v) not in declared]


def unmatched(fields: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    """ENTRY_UNMATCHED - the crosswalk outlives what it types."""
    present = set(fields)
    return [f"ENTRY_UNMATCHED: the crosswalk types {e.get('field')}: {e.get('value')} and "
            "STATUS.yaml does not carry it"
            for e in entries if (e.get("field"), e.get("value")) not in present]


def subject_not_derived(_f: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    """SUBJECT_NOT_DERIVED - a freely declared subject could dissolve a collision."""
    return [f"SUBJECT_NOT_DERIVED: {e.get('field')} declares subject {e.get('subject')!r} "
            f"and its field yields {derived_subject(e.get('field', ''))!r}"
            for e in entries if e.get("subject") != derived_subject(e.get("field", ""))]


def kind_undeclared(_f: list[tuple[str, str]], entries: list[dict], contract: dict) -> list[str]:
    """CLAIM_KIND_UNDECLARED - a typo here would silently disable the kind rules below."""
    kinds = set(contract["claim_kinds"])
    return [f"CLAIM_KIND_UNDECLARED: {e.get('field')} declares kind {e.get('claim_kind')!r}, "
            f"which is not one of {', '.join(sorted(kinds))}"
            for e in entries if e.get("claim_kind") not in kinds]


def collision(_f: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    """CLAIM_KIND_COLLISION - the real duplicate, which typing does not excuse.

    Two identical entries share a subject and a kind, so this also refuses the same field
    and value typed twice; that needs no refusal of its own.
    """
    seen: dict[tuple, int] = {}
    for entry in entries:
        key = (entry.get("subject"), entry.get("claim_kind"))
        seen[key] = seen.get(key, 0) + 1
    return [f"CLAIM_KIND_COLLISION: subject {subject} carries {count} {kind} claims; one "
            "subject holds at most one claim of a kind"
            for (subject, kind), count in sorted(seen.items()) if count > 1]


def kind_contradicts(_f: list[tuple[str, str]], entries: list[dict], contract: dict) -> list[str]:
    """CLAIM_KIND_CONTRADICTS_VALUE - total in both directions, and case-insensitive."""
    defects = []
    for entry in entries:
        if entry.get("claim_kind") not in contract["claim_kinds"]:
            continue  # already refused as CLAIM_KIND_UNDECLARED; one defect earns one code
        wanted = expected_kind(entry.get("value", ""))
        if entry.get("claim_kind") != wanted:
            defects.append(f"CLAIM_KIND_CONTRADICTS_VALUE: {entry.get('field')} carries "
                           f"{entry.get('value')} and declares {entry.get('claim_kind')}; "
                           f"that prefix admits only {wanted}")
    return defects


def reference_contradicts(_f: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    """REFERENCE_CONTRADICTS_VALUE - the packet id an entry names must be the one it carries.

    `reference` is load-bearing for owner acceptance: the contract says it names the packet.
    A field the contract calls load-bearing and grades nowhere is a declaration, which is
    what this table exists to stop.
    """
    defects = []
    for entry in entries:
        found = tokens(entry.get("value", ""))
        carried = (PACKET_TOKEN.match(found[2])
                   if found[:2] == ["OWNER", "ACCEPTED"] and len(found) > 2 else None)
        named = PACKET_REFERENCE.match(str(entry.get("reference") or ""))
        if carried and (not named or named.group(1) != carried.group(1)):
            defects.append(f"REFERENCE_CONTRADICTS_VALUE: {entry.get('field')} carries packet "
                           f"A{carried.group(1)} and names {entry.get('reference')!r}")
        elif named and not carried:
            defects.append(f"REFERENCE_CONTRADICTS_VALUE: {entry.get('field')} names packet "
                           f"{entry.get('reference')} and its value carries none")
    return defects


CHECKS = (malformed, unknown_key, untyped, unmatched, subject_not_derived,
          kind_undeclared, collision,
          kind_contradicts, reference_contradicts)
