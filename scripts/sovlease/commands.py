"""What each lease command does.

Split from the command line for the same reason the session package splits it: a hook or a
test that already knows what it wants should reach the behaviour without building an
argument parser.

Every command that changes anything appends an event. Nothing here edits a line, and
nothing here grants anything - `take` records that a participant is holding a concern
inside an envelope, which is a statement about responsibility, not about permission.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any
import argparse
import json

from sovkernel import lease_budget
from sovkernel import work_lease
from sovlease import store
from sovsession import commands as session_commands
from sovsession import store as session_store

DEFAULT_MINUTES = 120
CONTRACT = "contracts/work-lease.schema.json"


class LeaseError(RuntimeError):
    """The command could not be carried out against the current record."""


def _emit(payload: Any, as_json: bool, text: str = "") -> None:
    """Print machine output or human output, never both."""
    print(json.dumps(payload, indent=2, sort_keys=True) if as_json else text)


def _pairs(values: list[str] | None, key: str, cast) -> list[dict[str, Any]]:
    """Read `name=limit` options into budget entries, refusing a malformed one."""
    entries = []
    for item in values or []:
        name, _, amount = item.partition("=")
        if not amount:
            raise LeaseError(f"{item!r} is not name=amount")
        entries.append({key: name.strip(), "limit": cast(amount)})
    return entries


def _definition(args: argparse.Namespace) -> dict[str, Any]:
    """What this invocation derives from, as the holder declares it."""
    definition = {
        "definition_id": args.definition,
        "definition_kind": args.definition_kind,
        "provenance": args.provenance,
        "version": args.definition_version,
    }
    if args.derives_from:
        definition["derives_from"] = args.derives_from
    if args.definition_source:
        definition["source"] = args.definition_source
    return definition


def _grant(args: argparse.Namespace) -> dict[str, Any]:
    """A grant, or the honest absence of one.

    Absence is the ordinary case and is recorded as such rather than as an empty grant
    that reads like a granted one. A holder with no grant may still hold a lease and may
    still do nothing beyond the local record.
    """
    if not args.grant:
        return {"grant_id": None, "authority_type": None, "capabilities": [],
                "effect_ceiling": "RECORD_LOCAL"}
    return {"grant_id": args.grant, "authority_type": args.authority_type,
            "capabilities": sorted(set(args.capability or [])),
            "effect_ceiling": args.effect_ceiling}


def _build(args: argparse.Namespace, lease_id: str, session: str, relation: str,
           parent: str | None, controller: str | None, fence: int) -> dict[str, Any]:
    """Assemble one lease record in the shape the contract declares."""
    granted = session_store.now()
    expires = (session_store.parse_time(granted)
               + timedelta(minutes=args.minutes)).isoformat(timespec="seconds")
    concern: dict[str, Any] = {"kind": args.concern_kind, "reference": args.reference}
    if args.capability_served:
        concern["capability"] = args.capability_served
    return {
        "lease_schema": "soveraeign-work-lease/v1",
        "status": "PROPOSED",
        "lease_id": lease_id,
        "concern": concern,
        "holder": {
            "principal_id": args.principal or store.principal_id(session),
            "relation": relation,
            "parent_lease": parent,
            "controller_principal": controller,
            "session": session,
            "definition": _definition(args),
        },
        "grant": _grant(args),
        "budget": {
            "consumption": _pairs(args.budget, "dimension", float),
            "emission": _pairs(args.emit, "counter", int),
        },
        "closure": {"condition": args.closure, "defeating_evidence": args.defeat},
        "fence": fence,
        "granted_at": granted.replace("+00:00", "Z"),
        "expires_at": expires.replace("+00:00", "Z"),
        "state": "HELD",
    }


def _validate(lease: dict[str, Any], root: Path) -> None:
    """Refuse to record a lease the contract would reject."""
    from sovkernel.jsonschema import validate

    with (root / CONTRACT).open(encoding="utf-8") as handle:
        defects = validate(lease, json.load(handle))
    if defects:
        raise LeaseError("the lease does not satisfy " + CONTRACT + ":\n  "
                         + "\n  ".join(defects))


def _context(name: str | None = None) -> tuple[Path, Path, str]:
    root = session_store.repo_root()
    return root, store.store_dir(), session_commands.session_name(name)


def cmd_take(args: argparse.Namespace) -> int:
    """Open a lease over one concern, held by this session's instance principal."""
    root, directory, session = _context(args.name)
    existing = store.leases(directory)
    lease_id = "lease:" + store.slug(args.lease_id or args.reference)
    lease = _build(args, lease_id, session, "PARENT", None, args.controller,
                   store.next_fence(existing, lease_id))
    _validate(lease, root)
    store.append(directory, store.LEASES_LOG,
                 {"event": "take", "lease_id": lease_id, "session": session, "lease": lease})
    _emit(lease, args.as_json,
          f"{lease_id} held by {lease['holder']['principal_id']} until {lease['expires_at']}")
    return 0


def cmd_helper(args: argparse.Namespace) -> int:
    """Open a subordinate lease under a parent, bounded by what the parent holds."""
    root, directory, session = _context(args.name)
    existing = store.leases(directory)
    parent = existing.get(args.parent)
    if parent is None:
        raise LeaseError(f"{args.parent} is not a recorded lease")
    stem = args.lease_id or (args.parent.removeprefix("lease:") + "-" + args.reference)
    lease_id = "lease:" + store.slug(stem)
    # A helper is a different invocation, so it is a different principal. Deriving it from
    # the session plus the part being handed over keeps that true by default: without it a
    # session would witness its own work and the self-witness check would never fire.
    args.principal = args.principal or store.principal_id(
        session + "." + store.slug(args.reference))
    lease = _build(args, lease_id, session, args.relation, args.parent,
                   parent["holder"]["principal_id"], store.next_fence(existing, lease_id))
    _validate(lease, root)
    defects = work_lease.evaluate(lease, parent=parent)
    if defects:
        _emit([defect._asdict() for defect in defects], args.as_json,
              "\n".join(f"REFUSED {d.code}: {d.message}" for d in defects))
        return 1
    store.append(directory, store.LEASES_LOG,
                 {"event": "helper", "lease_id": lease_id, "session": session,
                  "parent_lease": args.parent, "lease": lease})
    _emit(lease, args.as_json, f"{lease_id} recruited under {args.parent}")
    return 0


def cmd_draw(args: argparse.Namespace) -> int:
    """Record consumption or emission against a lease, then report where that leaves it."""
    _, directory, session = _context(args.name)
    leases = store.leases(directory)
    lease = leases.get(args.lease)
    if lease is None:
        raise LeaseError(f"{args.lease} is not a recorded lease")
    for entry in _pairs(args.consume, "dimension", float):
        store.append(directory, store.DRAWS_LOG,
                     {"lease_id": args.lease, "kind": "consumption", "session": session,
                      "dimension": entry["dimension"], "amount": entry["limit"],
                      "measured_by": args.measured_by})
    for entry in _pairs(args.produce, "counter", int):
        store.append(directory, store.DRAWS_LOG,
                     {"lease_id": args.lease, "kind": "emission", "session": session,
                      "counter": entry["counter"], "amount": entry["limit"],
                      "measured_by": args.measured_by})
    return _report(directory, lease, args.as_json)


def _report(directory: Path, lease: dict[str, Any], as_json: bool) -> int:
    """One lease's envelope and what anybody watching should notice about it."""
    accounted = lease_budget.account(lease, store.draws(directory))
    readings = lease_budget.readings(lease, store.draws(directory))
    payload = {"lease": lease["lease_id"], "account": accounted, "readings": readings,
               "pressure": lease_budget.pressure(accounted, lease)}
    lines = [f"{lease['lease_id']} at {payload['pressure']:.0%} of its tightest bound"]
    lines += [f"  {name}: {amount} left" for name, amount in sorted(
        accounted["remaining"].items())]
    lines += [f"  {reading['code']}: {reading['message']}" for reading in readings]
    _emit(payload, as_json, "\n".join(lines))
    return 0


def cmd_close(args: argparse.Namespace) -> int:
    """Declare closure with evidence, refusing the claim the record cannot support."""
    _, directory, _ = _context(args.name)
    leases = store.leases(directory)
    lease = leases.get(args.lease)
    if lease is None:
        raise LeaseError(f"{args.lease} is not a recorded lease")
    candidate = dict(lease)
    candidate["state"] = "COMPLETED"
    candidate["closure_evidence"] = {
        "receipt_id": args.receipt, "standing_reached": args.standing,
        "evidence_addresses": list(args.evidence), "witnessed_by": args.witnessed_by}
    children = [other for other in leases.values()
                if other.get("holder", {}).get("parent_lease") == args.lease]
    # A helper closing itself is still a helper: its parent has to be supplied, or the
    # evaluator reads it as an orphan and refuses the one transition it should allow.
    parent = leases.get(candidate.get("holder", {}).get("parent_lease") or "")
    defects = work_lease.evaluate(candidate, parent=parent, children=children)
    if defects:
        _emit([defect._asdict() for defect in defects], args.as_json,
              "\n".join(f"REFUSED {d.code}: {d.message}" for d in defects))
        return 1
    store.append(directory, store.LEASES_LOG,
                 {"event": "close", "lease_id": args.lease,
                  "closure_evidence": candidate["closure_evidence"]})
    _emit(candidate, args.as_json, f"{args.lease} closed at {args.standing}")
    return 0


def cmd_release(args: argparse.Namespace) -> int:
    """Give a lease back without claiming the concern is finished."""
    _, directory, _ = _context(args.name)
    store.append(directory, store.LEASES_LOG, {"event": "release", "lease_id": args.lease})
    _emit({"lease": args.lease, "state": "RELEASED"}, args.as_json,
          f"{args.lease} released; the concern is unheld and still open")
    return 0


def cmd_fail(args: argparse.Namespace) -> int:
    """Stop short and say so, which is a different record from releasing."""
    _, directory, _ = _context(args.name)
    store.append(directory, store.LEASES_LOG,
                 {"event": "fail", "lease_id": args.lease, "reason": args.reason})
    _emit({"lease": args.lease, "state": "FAILED", "reason": args.reason}, args.as_json,
          f"{args.lease} failed: {args.reason}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Who is holding what, inside which envelope, and what nobody is holding any more."""
    _, directory, _ = _context(args.name)
    leases = store.leases(directory)
    live = {name for name, record in session_store.sessions(directory).items()
            if record.get("live")}
    drawn = store.draws(directory)
    verdicts = work_lease.evaluate_set(leases.values())
    rows = []
    for lease_id, lease in sorted(leases.items()):
        if args.lease and lease_id != args.lease:
            continue
        if lease.get("state") in store.CLOSED_STATES and not args.all:
            continue
        accounted = lease_budget.account(lease, drawn)
        rows.append({
            "lease": lease_id,
            "state": lease.get("state"),
            "holder": lease.get("holder", {}).get("principal_id"),
            "session_live": (lease.get("holder", {}).get("session") or "") in live,
            "pressure": lease_budget.pressure(accounted, lease),
            "readings": lease_budget.readings(lease, drawn),
            "defects": [defect._asdict() for defect in verdicts.get(lease_id, [])],
        })
    payload = {"leases": rows, "orphaned": store.orphaned(directory, live)}
    lines = [f"{row['lease']} {row['state']} {row['holder']} "
             f"{'live' if row['session_live'] else 'SESSION GONE'} "
             f"{row['pressure']:.0%}" for row in rows] or ["no leases held"]
    for row in rows:
        lines += [f"  {item['code']}: {item['message']}"
                  for item in row["readings"] + row["defects"]]
    _emit(payload, args.as_json, "\n".join(lines))
    return 0
