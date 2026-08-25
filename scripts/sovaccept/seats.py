"""Resolve the owner edge from contracts/seat-registry.json.

Owner is a seat, not a person: ``owner(X)`` is the seat one edge up, the one
that issued X's grant and settles X's receipts (``decisions/0020``). Ownership
does not chain -- the root seat accepts what the control seat presents and never
reaches past it to accept a worker's report -- so every question here is asked
about exactly one edge.
"""

from __future__ import annotations

from pathlib import Path
import json


class SeatError(ValueError):
    """A seat was named that the registry does not carry."""


def load(root: Path) -> dict:
    """The current seat registry view."""
    return json.loads(
        (root / "contracts" / "seat-registry.json").read_bytes().decode("utf-8"))


def index(registry: dict) -> dict[str, dict]:
    """Seats by id."""
    return {seat["seat_id"]: seat for seat in registry["seats"]}


def seat(registry: dict, seat_id: str) -> dict:
    """One seat, or a refusal naming the seat that is absent."""
    found = index(registry).get(seat_id)
    if found is None:
        raise SeatError(f"{seat_id} is not a seat in contracts/seat-registry.json")
    return found


def owner_of(registry: dict, seat_id: str) -> str | None:
    """The seat one edge up, or None for the root seat."""
    return seat(registry, seat_id).get("owner_seat")


def occupant_id(registry: dict, seat_id: str) -> str | None:
    """The actor currently claiming the seat, if any claims it."""
    occupant = seat(registry, seat_id).get("occupant")
    return occupant["actor_id"] if occupant else None


def settles(registry: dict, seat_id: str) -> list[str]:
    """What the seat may settle: JUDGEMENT, VERIFICATION, or nothing."""
    return list(seat(registry, seat_id).get("settles") or [])


def edge_refusals(registry: dict, presenting: str, accepting: str,
                  claim_type: str) -> list[str]:
    """Why this pair is not a legal acceptance edge, if it is not."""
    problems = []
    try:
        expected = owner_of(registry, presenting)
    except SeatError as error:
        return [f"UNKNOWN_SEAT: {error}"]
    if presenting == accepting:
        problems.append(
            "SELF_ACCEPTANCE_REFUSED: the accepting seat is the presenting seat; "
            "no seat settles its own output")
    elif accepting != expected:
        problems.append(
            f"ACCEPTANCE_BY_NON_OWNER: {presenting} is owned by {expected}, not {accepting}; "
            "ownership is one edge up and does not chain")
    try:
        can_settle = settles(registry, accepting)
    except SeatError as error:
        return problems + [f"UNKNOWN_SEAT: {error}"]
    if claim_type not in can_settle:
        problems.append(
            f"ACCEPTANCE_SEAT_CANNOT_SETTLE: {accepting} settles "
            f"{can_settle or 'nothing'}, not {claim_type}")
    if occupant_id(registry, accepting) is None:
        problems.append(f"UNOCCUPIED_SEAT: {accepting} has no recorded occupant")
    return problems
