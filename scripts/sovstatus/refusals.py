"""The refusals a status-claim crosswalk entry can earn, and the derivations behind them.

Kept apart from `scripts/sov_status_claims.py` so the table can grow without dragging the
reader and the command line past the module budget with it. The reader owns what counts as
a status field; this owns what counts as a wrong entry.

The governing idea is that nothing an entry declares is trusted where it can be derived.
The subject is the field stem, the claim kind is fixed by the value's own prefix, and a
standing must appear in the value as a whole token that is not denied. An independent
witness defeated an earlier draft that let an entry declare a standing the value denied, so
the only admissible source is now the token itself.
"""

from __future__ import annotations

import re

ACCEPTANCE_VALUE = re.compile(r"^OWNER_ACCEPTED_A\d")
SUFFIX = "_status"
SHAPE = {"field": str, "value": str, "subject": str, "claim_kind": str, "detail": str}


def token_asserts(value: str, standing: str) -> bool:
    """Whether `value` carries `standing` as a whole token that is not denied.

    `NOT_WITNESSED` contains the token `WITNESSED` and asserts the opposite (CLAUDE.md T3),
    so a token preceded by `NOT` is a denial rather than a claim.
    """
    tokens = value.upper().split("_")
    return any(token == standing and (index == 0 or tokens[index - 1] != "NOT")
               for index, token in enumerate(tokens))


def derived_subject(field: str) -> str:
    """The only subject a field admits: its stem, with underscores hyphenated."""
    return field[: -len(SUFFIX)].replace("_", "-") if field.endswith(SUFFIX) else field


def expected_kind(value: str) -> str:
    """The only claim kind a value's own prefix admits. Total over every value."""
    if value.startswith("RULED_"):
        return "RULING"
    if ACCEPTANCE_VALUE.match(value):
        return "OWNER_ACCEPTANCE"
    return "STATUS"


def malformed(_f: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    """ENTRY_MALFORMED - an entry that would otherwise raise instead of refusing."""
    defects = []
    for index, entry in enumerate(entries):
        bad = [k for k, kind in SHAPE.items() if not isinstance(entry.get(k), kind)]
        if bad:
            defects.append(f"ENTRY_MALFORMED: entry {index} lacks well-formed {', '.join(bad)}")
        elif "artifact_standing" not in entry or "standing_source" not in entry:
            defects.append(f"ENTRY_MALFORMED: entry {index} ({entry['field']}) omits a "
                           "standing declaration")
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
    and value being typed twice; that needs no refusal of its own.
    """
    seen: dict[tuple, int] = {}
    for entry in entries:
        key = (entry.get("subject"), entry.get("claim_kind"))
        seen[key] = seen.get(key, 0) + 1
    return [f"CLAIM_KIND_COLLISION: subject {subject} carries {count} {kind} claims; one "
            "subject holds at most one claim of a kind"
            for (subject, kind), count in sorted(seen.items()) if count > 1]


def kind_contradicts(_f: list[tuple[str, str]], entries: list[dict], contract: dict) -> list[str]:
    """CLAIM_KIND_CONTRADICTS_VALUE - total in both directions, not just ruling against packet."""
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


def not_in_ladder(_f: list[tuple[str, str]], entries: list[dict], contract: dict) -> list[str]:
    """STANDING_NOT_IN_LADDER - a rung cannot be minted by typing one."""
    ladder = contract["artifact_standing_ladder"]
    return [f"STANDING_NOT_IN_LADDER: {e.get('field')} declares standing "
            f"{e.get('artifact_standing')!r}, which is not one of {', '.join(ladder)}"
            for e in entries
            if e.get("artifact_standing") is not None
            and e.get("artifact_standing") not in ladder]


def without_token(_f: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    """STANDING_WITHOUT_TOKEN - the door the witness came through.

    An earlier draft admitted an unverifiable `READING` source, and a standing declared
    under it was never compared to the value. A standing the document does not carry as a
    token is not asserted here at all.
    """
    defects = []
    for entry in entries:
        standing, source = entry.get("artifact_standing"), entry.get("standing_source")
        if standing is not None and source != "TOKEN":
            defects.append(f"STANDING_WITHOUT_TOKEN: {entry.get('field')} declares standing "
                           f"{standing} with source {source!r}; only a token asserts one")
        elif standing is None and source == "TOKEN":
            defects.append(f"STANDING_WITHOUT_TOKEN: {entry.get('field')} declares a TOKEN "
                           "source and no standing to find")
    return defects


def token_absent(_f: list[tuple[str, str]], entries: list[dict], _c: dict) -> list[str]:
    """STANDING_TOKEN_ABSENT - the token is missing, or the value denies it."""
    return [f"STANDING_TOKEN_ABSENT: {e.get('field')} declares standing "
            f"{e.get('artifact_standing')} from a token, and {e.get('value')} does not "
            "assert it undenied"
            for e in entries
            if e.get("standing_source") == "TOKEN"
            and isinstance(e.get("artifact_standing"), str)
            and not token_asserts(e.get("value", ""), e["artifact_standing"])]


def leading_untyped(_f: list[tuple[str, str]], entries: list[dict], contract: dict) -> list[str]:
    """LEADING_TOKEN_UNTYPED - a value that opens with a rung must be typed from it."""
    ladder = set(contract["artifact_standing_ladder"])
    return [f"LEADING_TOKEN_UNTYPED: {e.get('field')} begins with the ladder word "
            f"{e.get('value', '').split('_')[0]} and declares source {e.get('standing_source')}"
            for e in entries
            if e.get("value", "").upper().split("_")[0] in ladder
            and e.get("standing_source") != "TOKEN"]


CHECKS = (malformed, untyped, unmatched, subject_not_derived, kind_undeclared, collision,
          kind_contradicts, not_in_ladder, without_token, token_absent, leading_untyped)
