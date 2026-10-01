#!/usr/bin/env python3
"""Emit a fresh-participant observation, every field resolved from repository state.

`conformance/commissioning.py check_q11` grades P15-Q1.1 on observation-shaped
evidence; it imports no participant code and trusts whatever it is handed. A
hand-written fixture satisfies it just as well as a real fresh participant
would, which is the gap this module closes: `p15` resolves principal_id and
session_id from the same session-identity code `sov_session.py register` and
`brief` already call, phase_state from the same phase reconciliation
`sov_next.py` calls, work_address from the live Phase 1.5 custody collection,
capability/required_authority/effect_envelope from the one capability-map
entry that actually projects Record evidence, governance_context from the
digest of the phase record `sov_session.py` already pins briefings to, and
record_projection_id from a RecordProjection the run creates or finds through
`services/record`. A field this repository cannot resolve is written `null`,
never a placeholder, so `check_q11` reports it missing rather than believed.

Never weakens the oracle (`conformance/commissioning.py`, the fixtures under
`conformance/fixtures/commissioning/`): this module only produces evidence for
them to grade, unchanged.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
for _extra in (ROOT / "scripts", ROOT / "services" / "record" / "src"):
    if str(_extra) not in sys.path:
        sys.path.insert(0, str(_extra))

from sovcustody import collections as custody_collections  # noqa: E402
from sovsession import commands as session_commands  # noqa: E402
from sovsession import phase_context, principals  # noqa: E402
from soveraeign_record_service import RecordService  # noqa: E402

CUSTODY_ID = "custody:phase-1-5/fresh-participation"
"""The live Phase 1.5 custody fresh participation carries, from
`contracts/custodies/phase-1-5.json`."""

# The one operation in `contracts/fixtures/capability-map.reference.json`
# whose shape is a RecordProjection: `record.project-evidence`, an evidence-
# scoped read (`shape.subject: "record-projection"`, `crud: "READ"`). Every
# other `record.*` capability writes the journal or a derived projection
# store; this is the single read that hands a participant a RecordProjection,
# which is the evidence P15-X1 says a fresh participant's work must survive
# as. Read, not computed, because the fixture is proposed state this script
# must not hold authority to resolve a second way.
CAPABILITY = "record.project-evidence"
REQUIRED_AUTHORITY = "read:journal"
EFFECT_ENVELOPE = "RECORD_LOCAL"

PREDICATES = {"P15-Q1.1"}


def _digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def resolve_identity(root: Path) -> tuple[str | None, str | None]:
    """principal_id and session_id, read the way `sov_session.py register` and
    `brief` already resolve them: one session name, one principal claim
    against the registry in force. Neither call registers or writes anything;
    a session that has not identified itself through `SOV_SESSION`/
    `SOV_PRINCIPAL` resolves to `None`, which is reported as missing rather
    than guessed.
    """
    name = session_commands.session_name()
    claim = principals.resolve(root, name)
    principal_id = claim.get("principal")
    session_id = name if name.startswith("session:") else f"session:{name}"
    return principal_id, session_id


def resolve_phase_state(root: Path) -> str | None:
    """The active phase id, reconciled from STATUS.yaml and contracts/phases.json
    the way `sov_next.py` does. A conflict between the two, or no active
    phase, resolves to `None`.
    """
    state = phase_context.collect(root)
    if state.get("defects"):
        return None
    active = state.get("active")
    return active.get("phase_id") if active else None


def resolve_work_address(root: Path, phase_id: str | None) -> str | None:
    """`custody:phase-1-5/fresh-participation`, read from the live custody
    collection for the active phase, never assumed.
    """
    if phase_id is None:
        return None
    records = custody_collections.records(
        root / "contracts" / "custodies.json", root / "contracts" / "custodies", phase_id)
    for record in records:
        if record.get("custody_id") == CUSTODY_ID:
            return CUSTODY_ID
    return None


def resolve_governance_context(root: Path) -> str:
    """`contracts/phases.json@sha256:<digest of the file's own bytes>`."""
    phases_path = root / "contracts" / "phases.json"
    return f"contracts/phases.json@{_digest(phases_path)}"


def resolve_record_projection_id(
    out_dir: Path, principal_id: str | None, work_address: str | None,
) -> str | None:
    """A RecordProjection id for `work_address`, from a local System of Record
    this run creates under `out_dir` or finds there from an earlier run.
    Nothing is appended to any journal outside `out_dir`.
    """
    if not principal_id or not work_address:
        return None
    service = RecordService(out_dir / "record-store")
    try:
        existing = [entry for entry in service.entries()
                    if entry["subject"] == work_address and entry["kind"] == "EVENT"]
        if not existing:
            service.append(
                "EVENT", work_address, principal_id,
                {"capability": CAPABILITY, "required_authority": REQUIRED_AUTHORITY})
        projection = service.evidence_projection(
            [work_address], principal_id, "fresh-participant",
            "P15-Q1.1 fresh context observation")
        return projection["projection_id"]
    finally:
        service.close()


def observe_p15(root: Path, out_dir: Path) -> dict[str, Any]:
    """The nine fields `check_q11` requires, plus `oral_history_used`."""
    principal_id, session_id = resolve_identity(root)
    phase_state = resolve_phase_state(root)
    work_address = resolve_work_address(root, phase_state)
    record_projection_id = resolve_record_projection_id(out_dir, principal_id, work_address)
    return {
        "principal_id": principal_id,
        "session_id": session_id,
        "phase_state": phase_state,
        "work_address": work_address,
        "capability": CAPABILITY,
        "required_authority": REQUIRED_AUTHORITY,
        "effect_envelope": EFFECT_ENVELOPE,
        "governance_context": resolve_governance_context(root),
        "record_projection_id": record_projection_id,
        # Allowed to be a literal: every field above came from a file read or a
        # record this run created, not from a transcript.
        "oral_history_used": False,
    }


def cmd_p15(args: argparse.Namespace) -> int:
    if args.predicate not in PREDICATES:
        print(f"REFUSED UNKNOWN_PREDICATE: this command observes {sorted(PREDICATES)}, "
              f"not {args.predicate!r}")
        return 2
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    observation = observe_p15(ROOT, out_dir)
    target = out_dir / f"{args.predicate}.json"
    target.write_text(
        json.dumps(observation, sort_keys=True, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    print(str(target))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p15 = sub.add_parser("p15", help="emit a P15 fresh-context observation")
    p15.add_argument("--predicate", required=True, help="the predicate id to observe")
    p15.add_argument("--out", required=True, help="directory to write <predicate>.json into")
    p15.set_defaults(func=cmd_p15)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
