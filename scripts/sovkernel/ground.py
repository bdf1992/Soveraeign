"""Judge the product ground, and the join between it and the product canon.

``GROUND.md`` owns the wording of what product Soveraeign is;
``contracts/product-ground.json`` owns the identifiers. This module owns the rules that
hold ground and canon together: every promise derives from at least one ground claim that
exists, every ground claim is realized by at least one promise, and the two records agree
on which epoch and which ground revision they are speaking from.

One rule here is a correction rather than a check. A promise classified
``IMPLEMENTATION_DERIVED`` is refused outright, because an implementation is evidence
about product intent and never authority for creating it. The enum value exists so the
classification can be written down honestly while it is being fixed; carrying one into an
accepted canon is the defect the value is there to name.

Nothing here grants anything. A ground claim realized by fifteen promises is still only a
claim about what product this is, and says nothing about whether any of it works.
"""

from __future__ import annotations

from typing import Any
import re

#: A rendering is `<revision>.<amendment>`. The whole part must equal the revision it
#: renders, because a rendering carries no change of meaning and cannot outrun one.
RENDERING = re.compile(r"^(?P<revision>[A-Z]+-[1-9][0-9]*)[.][0-9]+$")

#: Refused in an accepted canon. See the module docstring.
IMPLEMENTATION_ONLY = "IMPLEMENTATION_DERIVED"


def _rendering_revision(rendering: str) -> str | None:
    match = RENDERING.match(rendering)
    return match.group("revision") if match else None


def rendering_defects(record: dict[str, Any], label: str) -> list[str]:
    """A rendering must render the revision it claims, and never a different one."""
    rendered = _rendering_revision(record["rendering"])
    if rendered is None:
        return [f"MALFORMED_RENDERING: {label} rendering {record['rendering']!r} is not "
                f"<revision>.<amendment>"]
    if rendered != record["revision"]:
        return [f"RENDERING_MISMATCH: {label} is revision {record['revision']} rendered as "
                f"{record['rendering']}; a rendering carries no change of meaning and "
                f"cannot render a revision other than its own"]
    return []


def ground_defects(ground: dict[str, Any]) -> list[str]:
    """Rules internal to the ground record, before any canon is joined to it."""
    found = rendering_defects(ground, "GROUND")
    claims = [claim["ground_id"] for claim in ground["claims"]]
    seen: set[str] = set()
    for claim_id in claims:
        if claim_id in seen:
            found.append(f"DUPLICATE_GROUND: {claim_id} is declared more than once")
        seen.add(claim_id)
    for entry in ground["retired"]:
        if entry["id"] in seen:
            found.append(f"RETIRED_GROUND_REUSED: {entry['id']} is retired and declared "
                         f"again in the same revision; retired identifiers are never "
                         f"reused, because work attributed under one has to keep meaning "
                         f"what it meant")
    return found


def join_defects(canon: dict[str, Any], ground: dict[str, Any]) -> list[str]:
    """Every rule that needs both records in hand at once."""
    found: list[str] = []
    claims = {claim["ground_id"] for claim in ground["claims"]}
    retired = {entry["id"] for entry in ground["retired"]}

    if canon["ground_revision"] != ground["revision"]:
        found.append(f"GROUND_REVISION_MISMATCH: {canon['revision']} derives from "
                     f"{canon['ground_revision']} and the ground record is "
                     f"{ground['revision']}; a canon pinned to a revision that is not "
                     f"there is a canon whose promises may already mean something else")
    if canon["epoch"] != ground["epoch"]:
        found.append(f"EPOCH_MISMATCH: {canon['revision']} was written under "
                     f"{canon['epoch']} and the ground record is {ground['epoch']}; a "
                     f"changed epoch means a different product, not a later draft")

    realized: set[str] = set()
    for promise in canon["promises"]:
        label = promise["promise_id"]
        if promise["source"] == IMPLEMENTATION_ONLY:
            found.append(f"IMPLEMENTATION_DERIVED_PROMISE: {label} exists primarily "
                         f"because something was built that way. An implementation is "
                         f"evidence about product intent and never authority for creating "
                         f"it: ground it independently, mark it "
                         f"OWNER_CONFIRMATION_REQUIRED, or move it below canon altitude")
        for claim_id in promise["derives_from"]:
            if claim_id in retired:
                found.append(f"RETIRED_GROUND_DERIVATION: {label} derives from {claim_id}, "
                             f"which {ground['revision']} retired")
            elif claim_id not in claims:
                found.append(f"UNKNOWN_GROUND: {label} derives from {claim_id}, which the "
                             f"ground record does not declare")
            else:
                realized.add(claim_id)

    for claim_id in sorted(claims - realized):
        found.append(f"UNREALIZED_GROUND: {claim_id} is declared and no promise derives "
                     f"from it; ground carrying something the product does not undertake "
                     f"is ground that has stopped being about the product")
    return found


def acceptance_defects(record: dict[str, Any], label: str, recorded: str) -> list[str]:
    """An accepted revision must be recorded where it says it is recorded.

    Two places hold one fact - the artifact and `STATUS.yaml` - so something has to check
    they agree, which is the shape `decisions/0037` settled for the two ticket readers. An
    artifact that calls itself accepted while the acceptance record does not name that
    exact revision is the drift this refuses.
    """
    found: list[str] = []
    accepted = record.get("accepted")
    if record["status"] == "ACCEPTED":
        if accepted is None:
            return [f"UNRECORDED_ACCEPTANCE: {label} calls itself ACCEPTED and carries no "
                    f"acceptance record saying who accepted what, and when"]
        if accepted["revision"] != record["revision"]:
            found.append(f"ACCEPTANCE_REVISION_MISMATCH: {label} is {record['revision']} "
                         f"and its acceptance record names {accepted['revision']}; "
                         f"acceptance attaches to one exact revision")
        if accepted["epoch"] != record["epoch"]:
            found.append(f"ACCEPTANCE_EPOCH_MISMATCH: {label} is {record['epoch']} and its "
                         f"acceptance record names {accepted['epoch']}")
        if record["revision"] not in recorded:
            found.append(f"ACCEPTANCE_NOT_RECORDED: {label} says it was accepted and "
                         f"recorded in {accepted['recorded_in']}, which does not name "
                         f"{record['revision']}")
    elif accepted is not None:
        found.append(f"ACCEPTANCE_WITHOUT_STATUS: {label} carries an acceptance record and "
                     f"its status is {record['status']}")
    return found


def wording_defects(ground: dict[str, Any], wording: str) -> list[str]:
    """Every identifier in the record must appear in the document that owns its wording."""
    found = []
    for claim in ground["claims"]:
        if claim["ground_id"] not in wording:
            found.append(f"UNWORDED_GROUND: {claim['ground_id']} is declared in the record "
                         f"and absent from {ground['wording_owned_by']}")
    for key in ("epoch", "revision", "rendering"):
        if ground[key] not in wording:
            found.append(f"UNWORDED_{key.upper()}: {ground[key]} is absent from "
                         f"{ground['wording_owned_by']}")
    return found


def ground_reading(canon: dict[str, Any], ground: dict[str, Any]) -> list[dict[str, Any]]:
    """One row per ground claim: which promises carry it, and how they arrived."""
    rows = []
    for claim in ground["claims"]:
        carried = [promise for promise in canon["promises"]
                   if claim["ground_id"] in promise["derives_from"]]
        rows.append({
            "ground_id": claim["ground_id"],
            "statement": claim["statement"],
            "promises": [promise["promise_id"] for promise in carried],
            "sources": sorted({promise["source"] for promise in carried}),
        })
    return rows
