"""The refusals a status-claim crosswalk entry can earn, and the derivations behind them.

Kept apart from `scripts/sov_status_claims.py` so the table can grow without dragging the
reader and the command line past the module budget with it. The reader owns what counts as
a status field; this owns what counts as a wrong entry.

Nothing an entry declares is trusted where it can be derived. The subject is the field
stem. The claim kind is fixed by the value's own prefix. The standing is the value's
leading token or nothing at all.

That last rule is the third attempt, and the first two are why it is shaped this way. A
first draft let an entry declare a standing from prose, and a witness declared `WITNESSED`
on a value reading `NOT_WITNESSED`. A second draft compared the standing to a token and
treated a preceding `NOT` as denial, and a second witness walked through
`NOT_YET_WITNESSED`, `NEVER_WITNESSED`, `AWAITING_WITNESSED` and `BUILT-NOT_WITNESSED` -
the last one because splitting on underscores alone hides a hyphenated negator entirely.

Both drafts guarded the reported instance. A vocabulary of negations can always be extended
by one word, so this draft asks a question with no vocabulary in it: is the standing the
first thing the value says? A value that opens with `BUILT` is not denying `BUILT`, and a
value that opens with anything else asserts no standing here whatever else it contains.
Four interacting refusals collapse into that one biconditional.
"""

from __future__ import annotations

import re

ACCEPTANCE_VALUE = re.compile(r"^OWNER_ACCEPTED_A(\d+)")
PACKET_REFERENCE = re.compile(r"^A(\d+)$")
SEPARATORS = re.compile(r"[^A-Za-z0-9]+")
SUFFIX = "_status"
SHAPE = {"field": str, "value": str, "subject": str, "claim_kind": str, "detail": str}


def tokens(value: str) -> list[str]:
    """The value's tokens, upper-cased, split on every non-alphanumeric run.

    Splitting on underscores alone let `BUILT-NOT_WITNESSED` read as two tokens, so a
    negator written with a hyphen was never seen by a rule looking for one.
    """
    return [token for token in SEPARATORS.split(value.upper()) if token]


def leading_standing(value: str, ladder: set[str]) -> str | None:
    """The standing a value asserts: its first token, if that token is a rung."""
    found = tokens(value)
    return found[0] if found and found[0] in ladder else None


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
    upper = value.upper()
    if upper.startswith("RULED_"):
        return "RULING"
    if ACCEPTANCE_VALUE.match(upper):
        return "OWNER_ACCEPTANCE"
    return "STATUS"


def malformed(_f: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    """ENTRY_MALFORMED - an entry that would otherwise raise instead of refusing."""
    defects = []
    for index, entry in enumerate(entries):
        bad = [k for k, kind in SHAPE.items() if not isinstance(entry.get(k), kind)]
        if bad:
            defects.append(f"ENTRY_MALFORMED: entry {index} lacks well-formed {', '.join(bad)}")
        elif "artifact_standing" not in entry or "reference" not in entry:
            defects.append(f"ENTRY_MALFORMED: entry {index} ({entry['field']}) omits a "
                           "standing or a reference")
    return defects


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


def standing_not_leading(_f: list[tuple[str, str]], entries: list[dict],
                         contract: dict) -> list[str]:
    """STANDING_NOT_THE_LEADING_TOKEN - the whole standing rule, in both directions.

    A standing is declared if and only if the value's first token is a rung, and then it is
    that rung. No negation vocabulary, so no negation vocabulary to be short by one.
    """
    ladder = set(contract["artifact_standing_ladder"])
    defects = []
    for entry in entries:
        asserted = leading_standing(entry.get("value", ""), ladder)
        declared = entry.get("artifact_standing")
        if declared != asserted:
            defects.append(f"STANDING_NOT_THE_LEADING_TOKEN: {entry.get('field')} declares "
                           f"{declared!r} and {entry.get('value')} leads with "
                           f"{(tokens(entry.get('value', '')) or ['nothing'])[0]}, which "
                           f"asserts {asserted!r}")
    return defects


def reference_contradicts(_f: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    """REFERENCE_CONTRADICTS_VALUE - the packet id an entry names must be the one it carries.

    `reference` is load-bearing for owner acceptance: the contract says it names the packet.
    A field the contract calls load-bearing and grades nowhere is a declaration, which is
    what this table exists to stop.
    """
    defects = []
    for entry in entries:
        carried = ACCEPTANCE_VALUE.match(entry.get("value", "").upper())
        named = PACKET_REFERENCE.match(str(entry.get("reference") or ""))
        if carried and (not named or named.group(1) != carried.group(1)):
            defects.append(f"REFERENCE_CONTRADICTS_VALUE: {entry.get('field')} carries packet "
                           f"A{carried.group(1)} and names {entry.get('reference')!r}")
        elif named and not carried:
            defects.append(f"REFERENCE_CONTRADICTS_VALUE: {entry.get('field')} names packet "
                           f"{entry.get('reference')} and its value carries none")
    return defects


CHECKS = (malformed, untyped, unmatched, subject_not_derived, kind_undeclared, collision,
          kind_contradicts, standing_not_leading, reference_contradicts)
