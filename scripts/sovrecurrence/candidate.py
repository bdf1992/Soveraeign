"""Synthesize a candidate Definition from settled experience, and observe that it took none.

The candidate is derived, never authored: its claim is composed from what the settled
sources actually show, and its identity is a digest over the basis, so the same basis
yields the same proposal and a moved basis yields a different one.

It is emitted and not persisted. That is the point of the clause rather than a limitation
of the reader: a candidate Definition acquires standing through `submit_proposal` and then
`accept`, which are separate governed transitions held by a seat. Writing this object into
a governing path would be the very defeat P15-Q4.2 names, so the reader hands the
participant an object to carry through the ordinary authority path and stops there.

Whether synthesis changed policy or phase is *observed*, not asserted: the governing
records are digested before and after, and a moved digest is reported as a defect.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from sovrecurrence import experience

GOVERNING = ("STATUS.yaml", "contracts/phases.json", experience.CUSTODY_COLLECTION)
"""What synthesis must leave untouched: current standing, phase authority, and the
collection the basis was read from. A candidate that edits its own basis has rewritten the
rule that produced it."""

RECORDED = "RECORDED"


def _proposal_id(sources: list[dict[str, Any]]) -> str:
    """A deterministic identity for the candidate: a digest over its cited basis."""
    rolling = sha256()
    for source in sorted(sources, key=lambda item: str(item["address"])):
        rolling.update(f"{source['address']}\n{source['digest']}\n".encode("utf-8"))
    return f"proposal:recurrence/{rolling.hexdigest()[:16]}"


def _recurrence(gathered: dict[str, Any], collection: dict[str, Any]) -> dict[str, Any]:
    """What recurs across the settled sources, read from the clauses and their members."""
    all_clauses = [str(custody.get("exit_clause")) for custody in collection.get("custodies") or []
                   if isinstance(custody, dict) and custody.get("exit_clause")]
    settled = list(gathered["clauses"])
    unsettled = [clause for clause in all_clauses if clause not in settled]
    return {
        "clauses_total": len(all_clauses),
        "clauses_with_settled_experience": settled,
        "clauses_without": unsettled,
        "sources_per_clause": {clause: sum(1 for source in gathered["sources"]
                                           if source["clause"] == clause) for clause in settled},
    }


def _claim(recurs: dict[str, Any]) -> str:
    """One sentence stating what the basis shows, composed from the basis and nothing else."""
    settled = ", ".join(recurs["clauses_with_settled_experience"]) or "none"
    without = ", ".join(recurs["clauses_without"]) or "none"
    return (
        f"{len(recurs['clauses_with_settled_experience'])} of {recurs['clauses_total']} exit "
        f"clauses carry settled experience ({settled}); {len(recurs['clauses_without'])} carry "
        f"none ({without}). Every clause that advanced did so through a member an independent "
        f"participant observed and that landed. The candidate Definition this recurrence "
        f"supports is that a clause carrying no such member has no path to its stage, so "
        f"admitting one is that clause's first unit of work rather than a question for a seat."
    )


def synthesize(root: Path, gathered: dict[str, Any],
               collection: dict[str, Any]) -> dict[str, Any]:
    """Compose the candidate from `gathered`, preserving every settled address as a source."""
    sources = gathered["sources"]
    recurs = _recurrence(gathered, collection)
    return {
        "proposal_id": _proposal_id(sources),
        "claim": _claim(recurs),
        "standing": RECORDED,
        "authority_effect": "NONE",
        "source_addresses": [source["address"] for source in sources],
        "cited_basis": {source["address"]: source["digest"] for source in sources},
        "recurs": recurs,
        "carried_by": None,
        "note": ("Emitted, not persisted. It becomes a Proposal only through submit_proposal "
                 "by a participant that holds the authority, and binds nothing until accept."),
    }


def governing_digests(root: Path) -> dict[str, str | None]:
    """The digest of each governing record, for comparison across synthesis."""
    return {relative: experience.digest(root / relative, root) for relative in GOVERNING}
