"""Walk JOURNEY-02 through the MCP binding, measure it, and record what came back.

A participant with no session and one grant. It asks the node what it can do, then reads
the journal back through a different endpoint to see what the crossing left behind.

The grant is the change Bdo's 2026-08-25 ruling made to this walk. `console.discover-
operations` declares `read:session` and, until that ruling, checked nothing, so the
walk recorded a participant holding nothing getting an answer. The operation now checks
what it declares, so the node's root issues `sov` that one grant before the crossing and
the observation records it rather than reporting a cost it no longer has.

Two artifacts come out of one run:

``observations/journey-02-discovery.json``
    what a participant holding nothing got out of the node, and the digests of the two
    journal entries the crossing left.

``observations/journey-02-receipt.json``
    a `contracts/receipt.schema.json` receipt for the same crossing, carrying what it
    served and what it actually consumed. `python scripts/sov_trace.py` walks that receipt
    up to the ground claim that justified it.

These are observations, not tests. The tests establish that the code does what it says;
this establishes that a participant with nothing can get an answer out of the node, and
that the answer cost something measurable.

It is not independent. It calls the gateway to observe the gateway, and reading the
journal back is a second endpoint rather than a second observer. Settling that needs the
Observation Service, which is a charter (`GROUND-010`).
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from gateway import Gateway  # noqa: E402

DISCOVERY = HERE / "observations" / "journey-02-discovery.json"
RECEIPT = HERE / "observations" / "journey-02-receipt.json"

#: What this crossing serves. One capability: what a run directly served is measured
#: once, and every broader intention containing it is a view rather than a second
#: expenditure.
SERVES = "console.discover-operations"
#: Who walks it, and the one grant the operation costs. Issued as setup before the
#: measured crossing, so the seconds below are the answer and not the permit.
WALKER = "sov"
REQUIRED_GRANT = "read:session"
#: Reading the journal back is a second crossing with its own declared cost. It is
#: setup for the observation, not part of the measured one.
JOURNAL_GRANT = "read:journal"
NODE = "node:local"


def _digest(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _stamp(seconds: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(seconds))


def _receipt(answer: dict, journal: list[dict], elapsed: float,
             started: float, grant_id: str) -> dict:
    """A schema-valid receipt for the crossing, carrying what it served and spent."""
    body = {
        "receipt_id": f"receipt_{journal[-1]['entry_digest'][:16]}",
        "event_id": journal[0]["entry_id"],
        "event_type": "console.discover-operations",
        "actor_id": "sov",
        "interface_id": "bindings/mcp:console_operations",
        "input_addresses": ["contracts/fixtures/capability-map.reference.json"],
        "input_state_digest": answer["capability_revision"],
        "authority_grant_ids": [grant_id],
        "precondition_results": [
            {"precondition": "session_live", "required": False,
             "note": "the manifest declares this endpoint requires_session false"},
            {"precondition": "live_matching_grant", "result": "SATISFIED",
             "note": f"{WALKER} holds {REQUIRED_GRANT} scoped to {WALKER}"},
            {"precondition": "capability_map_fresh", "result": "UNVERIFIED",
             "note": "the gateway read the projection and did not rebuild it"},
        ],
        "effect_class": "RECORD_LOCAL",
        "outcome": "COMMITTED",
        "emitted_record_addresses": [entry["entry_digest"] for entry in journal],
        "observed_evidence_addresses": ["bindings/mcp/observations/"
                                        "journey-02-discovery.json"],
        "created_at": _stamp(started),
        "serves_capability": SERVES,
        "consumed": [
            {"dimension": "wallclock_seconds", "amount": round(elapsed, 4),
             "measured_by": "time.perf_counter around gateway.call",
             "note": "the crossing alone. Opening the store is setup, not this operation"},
            {"dimension": "tool_calls", "amount": 1,
             "measured_by": "bindings/mcp/observe_journey_02.py"},
            {"dimension": "usd", "amount": 0,
             "measured_by": "bindings/mcp/observe_journey_02.py",
             "note": "a valuation of this usage at zero, not an absence of usage. "
                     "RECORD_LOCAL and no monetary charge; the seconds were still spent"},
        ],
    }
    body["receipt_digest"] = _digest(body)
    return body


def main() -> int:
    with TemporaryDirectory() as tmp:
        gateway = Gateway(Path(tmp) / "state")
        try:
            tools = {tool["name"] for tool in gateway.tools()}
            # Setup, not the crossing: the node's root records the one grant the
            # operation declares. The first grant against an empty journal also
            # records the root issuer (services/console .. authority.py, Bootstrap).
            grant_id = gateway.console.grant(WALKER, REQUIRED_GRANT, WALKER)["grant_id"]
            gateway.console.grant(WALKER, JOURNAL_GRANT, NODE)
            started = time.time()
            mark = time.perf_counter()
            answer = gateway.call("console_operations", {}, WALKER)
            elapsed = time.perf_counter() - mark
            entries = gateway.call("record_entries", {}, "sov")
        finally:
            gateway.close()

    crossing = [entry for entry in entries
                if entry.get("subject") == "discover-operations"]
    sample = next(row for row in answer["operations"]
                  if row["capability_id"] == SERVES)

    observation = {
        "observation": "JOURNEY-02 walked through the MCP binding by a fresh participant",
        "walked_by": "gateway.call, bindings/mcp/gateway.py",
        "participant": {"actor": WALKER, "session": None, "grants_held": 2,
                        "grants": [f"{REQUIRED_GRANT} scoped to {WALKER}",
                                   f"{JOURNAL_GRANT} scoped to {NODE}"]},
        "tool_surface": sorted(tools),
        "capability_revision": answer["capability_revision"],
        "counts": answer["counts"],
        "freshness": answer["freshness"],
        "omissions": answer["omissions"],
        "journal_entries_left_by_the_crossing": len(crossing),
        "journal": [{"seq": entry["seq"], "kind": entry["kind"],
                     "subject": entry["subject"], "actor": entry["actor"],
                     "entry_digest": entry["entry_digest"],
                     "payload": entry["payload"]}
                    for entry in crossing],
        "one_row": sample,
        "what_this_does_not_establish": [
            "that any reachable capability works; only that the node declares it and the "
            "projection records a transport",
            "that the capability map is current, which nobody checked on this call",
            "that a participant holding nothing can get an answer. It cannot any more: "
            "the operation checks the read:session it declares, and this walk issued "
            "that grant as setup before measuring the crossing",
            "that reading the journal back is free. It costs read:journal over the "
            "node, checked against the node's own authority store since 2026-08-25; "
            "the walk holds that grant too and only the discovery crossing is timed",
            "that this observation is independent of the gateway - it was taken by "
            "calling the gateway. The journal read is a second endpoint, not a second "
            "observer, and settling this needs the Observation Service (GROUND-010)",
        ],
    }

    DISCOVERY.parent.mkdir(parents=True, exist_ok=True)
    DISCOVERY.write_text(json.dumps(observation, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8", newline="\n")
    RECEIPT.write_text(
        json.dumps(_receipt(answer, crossing, elapsed, started, grant_id), indent=2,
                   ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    print(f"declared {answer['counts']['declared']}, "
          f"reachable {answer['counts']['reachable']}, "
          f"{len(crossing)} journal entries, {elapsed:.4f}s")
    print(f"wrote {DISCOVERY.relative_to(ROOT)}")
    print(f"wrote {RECEIPT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
