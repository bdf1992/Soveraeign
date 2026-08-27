"""Read run history out of wherever it lives today, and say where that is.

This module is the seam. Every health rule in ``contracts/automation-health.json``
is stated over ``Run`` records rather than over files, so moving the surface onto
the Console - reading what ``services/automation/`` owns through the Record
Service - replaces this module and leaves ``health.py``, the rules, and the
fixture corpus untouched.

Today the records are the harness ledger under ``.local/schedules/``, which is
gitignored machine-local state. That is why ``LedgerState`` exists: a reader that
cannot tell "no runs have happened" from "this machine holds no history" will
report the second as the first, and the page would then be graded as current on a
machine that never had the bytes to grade.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import hashlib

from sovschedule import ledger

#: scripts/sovschedule/runner.py writes this prefix ahead of a refusal's reason code.
#: The coupling is asserted in scripts/tests/test_automation_health.py by driving the
#: real runner into a refusal, so a change to the runner's wording fails there rather
#: than silently turning every refusal into an unparseable one here.
REFUSAL_PREFIX = "refused before invocation: "
#: The same coupling on the REPORTED event, where the executor's exit code lives.
#: 124 is a timeout and 127 is "claude is not on this machine"; both otherwise read as
#: an ordinary failure, and a reader chasing a broken schedule would never see it.
EXIT_PREFIX = "executor exit code "
REPORTS_DIR = "reports/"

ATTEMPTED = "ATTEMPTED"
REPORTED = "REPORTED"
REFUSED = "REFUSED"


@dataclass(frozen=True)
class Run:
    """One scheduled run as the ledger holds it: an attempt, and a report or nothing."""

    run_id: str
    attempted_at: datetime
    attempt_outcome: str
    reason_code: str | None
    reported_at: datetime | None
    report_outcome: str | None
    exit_code: int | None = None
    #: Output addresses the REPORTED event recorded: the run capture, any report the
    #: executor wrote, and the post-run tree digest.
    outputs: tuple[str, ...] = ()

    @property
    def produced_reports(self) -> bool:
        """Whether the run left a completion report behind, which every schedule asks for."""
        return any(address.startswith(REPORTS_DIR) for address in self.outputs)

    @property
    def duration_seconds(self) -> float | None:
        """Wall seconds between the attempt and the report, or None if none arrived."""
        if self.reported_at is None:
            return None
        return (self.reported_at - self.attempted_at).total_seconds()

    def age_seconds(self, now: datetime) -> float:
        return (now - self.attempted_at).total_seconds()


@dataclass(frozen=True)
class LedgerState:
    """Whether this machine holds run history at all, and the exact bytes if so."""

    present: bool
    digest: str
    entries: int
    path: str

    @property
    def absent_reason(self) -> str | None:
        """Why the history-derived rules could not be evaluated, or None."""
        if self.present:
            return None
        return (f"{self.path} does not exist: no scheduled run has ever executed here, "
                "and this checkout holds no record of one that executed elsewhere")


#: The digest of an absent ledger. Named so the page can record "there was nothing to
#: read" as a value rather than as a missing field.
EMPTY_DIGEST = "sha256:" + hashlib.sha256(b"").hexdigest()


def ledger_state(root: Path) -> LedgerState:
    """Read the ledger's presence, byte digest, and line count without parsing it."""
    path = ledger.ledger_path(root)
    address = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
    if not path.is_file():
        return LedgerState(False, EMPTY_DIGEST, 0, address)
    raw = path.read_bytes()
    entries = len([line for line in raw.decode("utf-8").splitlines() if line.strip()])
    return LedgerState(True, "sha256:" + hashlib.sha256(raw).hexdigest(), entries, address)


def _exit_code(event: dict | None) -> int | None:
    """The executor's exit code as the REPORTED event recorded it, or None."""
    if not event:
        return None
    reason = event.get("reason", "")
    if not reason.startswith(EXIT_PREFIX):
        return None
    digits = reason[len(EXIT_PREFIX):].split(";", 1)[0].strip()
    return int(digits) if digits.lstrip("-").isdigit() else None


def _addresses(event: dict | None) -> tuple[str, ...]:
    if not event:
        return ()
    return tuple(str(record.get("address", "")) for record in event.get("outputs", ()))


def _reason_code(event: dict) -> str | None:
    """The refusal code the runner recorded, or None when the reason is not a refusal."""
    reason = event.get("reason", "")
    if reason.startswith(REFUSAL_PREFIX):
        return reason[len(REFUSAL_PREFIX):].strip() or None
    return None


def runs_for(root: Path, schedule: str) -> list[Run]:
    """Every recorded run of one schedule, oldest first, paired attempt to report.

    A ledger entry is one event, and one run leaves an ATTEMPTED event and then at
    most one REPORTED event. Pairing on ``run_id`` rather than on adjacency is what
    keeps a run readable when a second schedule interleaves with it, which is the
    ordinary case under a tick that fires several schedules in one minute.
    """
    attempts: dict[str, dict] = {}
    reports: dict[str, dict] = {}
    order: list[str] = []
    for entry in ledger.read(root, schedule):
        run_id = entry["run_id"]
        event = entry["event"]
        if event["event_phase"] == ATTEMPTED:
            if run_id not in attempts:
                order.append(run_id)
            attempts[run_id] = event
        elif event["event_phase"] == REPORTED:
            reports[run_id] = event
    runs = []
    for run_id in order:
        attempt = attempts[run_id]
        report = reports.get(run_id)
        runs.append(Run(
            run_id=run_id,
            attempted_at=ledger.parse_timestamp(attempt["occurred_at"]),
            attempt_outcome=attempt["outcome"],
            reason_code=_reason_code(attempt),
            reported_at=ledger.parse_timestamp(report["occurred_at"]) if report else None,
            report_outcome=report["outcome"] if report else None,
            exit_code=_exit_code(report),
            outputs=_addresses(report),
        ))
    return sorted(runs, key=lambda run: (run.attempted_at, run.run_id))


def from_records(records: list[dict]) -> list[Run]:
    """Build runs from declared fact records, for the fixture corpus and for tests.

    The corpus states what the ledger holds rather than writing a ledger, so the
    rules can be defeated on a machine where no scheduled run has ever happened -
    which is every machine this repository presently exists on.
    """
    runs = [
        Run(
            run_id=record["run_id"],
            attempted_at=ledger.parse_timestamp(record["attempted_at"]),
            attempt_outcome=record["attempt_outcome"],
            reason_code=record.get("reason_code"),
            reported_at=(ledger.parse_timestamp(record["reported_at"])
                         if record.get("reported_at") else None),
            report_outcome=record.get("report_outcome"),
            exit_code=record.get("exit_code"),
            outputs=tuple(record.get("outputs", ())),
        )
        for record in records
    ]
    return sorted(runs, key=lambda run: (run.attempted_at, run.run_id))


def newest(runs: list[Run]) -> Run | None:
    return runs[-1] if runs else None
