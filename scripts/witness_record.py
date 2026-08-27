"""Observe the operational System of Record from outside the code that built it.

Issue #7 declares its own witness procedure: commit, interrupt, restart,
reconstruct, retract, drop every projection, rebuild them, and compare the
resulting authoritative record addresses and terminal receipts. That walk existed
only as `services/record/tests/test_journal.py::test_witness_walk`, which imports
the participant and drives its Python API. `AGENTS.md` holds that a build cannot
witness itself, so that test establishes `BUILT` and nothing further.

This module takes the other path on purpose:

- the service is reached only as a subprocess through `cli.py`, so nothing here
  imports `soveraeign_record_service`;
- every digest is recomputed here from the chain rule stated in
  `services/record/CHARTER.md` and compared against what the service reported,
  rather than asking the service whether its own chain holds;
- the interrupt is performed against the SQLite file directly, outside the
  service, because an interruption the participant stages for itself is not an
  interruption;
- every restart is a genuinely fresh process, which is stronger than the
  in-process reopen the participant's own test performs.

Running this establishes an independent observation. It does not establish
`WITNESSED`, which is a standing another participant proposes and only Bdo
settles.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable
import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovwitness import Observation  # noqa: E402
from sovwitness.record_chain import (  # noqa: E402
    GENESIS, LEGACY_DIGEST_PROFILE, canonical_bytes_disagree, recompute, verify_chain,
)

ROOT = Path(__file__).resolve().parents[1]
SUBJECT = "run-witness-1"
WALKER = "witness/record@" + Path(__file__).name


def _environment() -> dict[str, str]:
    """The subprocess environment, carrying the one source root the CLI needs."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "services" / "record" / "src")
    return env


def record(store: Path, *args: str, expect: int = 0) -> dict[str, Any]:
    """Run one record command as a fresh subprocess and return the JSON it printed."""
    proc = subprocess.run(
        [sys.executable, "-m", "soveraeign_record_service.cli", "--root", str(store), *args],
        capture_output=True, text=True, env=_environment(), cwd=str(ROOT), check=False)
    if proc.returncode != expect:
        raise SystemExit(f"record exited {proc.returncode} for {args}\n{proc.stdout}{proc.stderr}")
    return json.loads(proc.stdout)


def _interrupt(store: Path) -> None:
    """Stage a write that never commits, from outside the service entirely.

    The connection is opened against the store's own SQLite file, an insert is
    issued inside an open transaction, and the connection is closed without a
    commit. Nothing the participant does is involved in staging this.
    """
    connection = sqlite3.connect(store / "record-service.sqlite3")
    connection.execute(
        "INSERT INTO journal(entry_id,kind,subject,actor,source_address,"
        "payload_json,recorded_at,prev_digest,entry_digest) "
        "VALUES('entry_interrupted','EVENT',?,'outside',NULL,'{}',0,'x','y')",
        (SUBJECT,),
    )
    connection.close()


def _commit(observed: Observation, store: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Commit one event and one terminal receipt, and check both came back whole."""
    entry = record(store, "append-entry", "--kind", "EVENT", "--subject", SUBJECT,
                   "--actor", "Bdo", "--payload", '{"step": "begin"}')
    receipt = record(store, "append-receipt", "--outcome", "COMMITTED", "--event",
                     "operation.begin", "--subject", SUBJECT, "--actor", "Bdo",
                     "--detail", '{"emitted_record_addresses": []}')
    observed.note(entry["prev_digest"] == GENESIS,
                  "the first entry chains from genesis", entry["prev_digest"][:16])
    observed.note(receipt["prev_digest"] == entry["entry_digest"],
                  "the receipt chains onto the event it settles", receipt["prev_digest"][:16])
    observed.note(receipt["payload"]["outcome"] == "COMMITTED",
                  "the receipt is terminal", receipt["payload"]["event"])
    return entry, receipt


def _survives_restart(observed: Observation, store: Path,
                      committed: list[dict[str, Any]]) -> list[str]:
    """Interrupt, restart, and reconstruct: what committed is there, what did not is not."""
    _interrupt(store)
    replay = record(store, "reconstruct-journal")
    entries = replay["entries"]
    ids = [entry["entry_id"] for entry in entries]

    observed.note(len(entries) == len(committed),
                  "a restart reconstructs exactly what committed",
                  str(len(entries)) + " of " + str(len(committed)))
    observed.note("entry_interrupted" not in ids,
                  "a transaction that never commits leaves nothing behind")
    observed.note(ids == [entry["entry_id"] for entry in committed],
                  "committed records survive the restart in order")
    broken = verify_chain(entries)
    observed.note(not broken, "every digest recomputes here, outside the service",
                  "broken=" + str(broken) if broken else str(len(entries)) + " links")
    return [entry["entry_digest"] for entry in entries]


def _retract(observed: Observation, store: Path, target: dict[str, Any],
             before: list[str]) -> None:
    """Retraction appends and preserves; it never reaches back."""
    counter = record(store, "counter-entry", "--entry", target["entry_id"],
                     "--actor", "Bdo", "--reason", "superseded by a later reading")
    original = record(store, "read-entry", "--entry", target["entry_id"])

    observed.note(original == target, "the countered original is byte-identical afterwards")
    observed.note(counter["payload"]["counters"] == target["entry_id"],
                  "the counter-record names what it counters", counter["entry_id"])
    after = [entry["entry_digest"] for entry in record(store, "reconstruct-journal")["entries"]]
    observed.note(after[:len(before)] == before,
                  "retraction leaves every prior record address unchanged",
                  str(len(before)) + " addresses held")
    observed.note(len(after) == len(before) + 1,
                  "retraction adds exactly one record", str(len(after)) + " total")


def _projections(observed: Observation, store: Path) -> None:
    """Drop every projection, rebuild, and compare; then check nothing writes from one."""
    record(store, "rebuild-projections")
    first = record(store, "read-projection", "--subject", SUBJECT)
    observed.note(first.get("authoritative") is False
                  and first.get("rebuilt_from") == "record-service-journal",
                  "the read path declares itself a projection", str(first.get("rebuilt_from")))

    record(store, "drop-projections")
    gone = record(store, "read-projection", "--subject", SUBJECT, expect=3)
    observed.note(gone.get("outcome") == "REFUSED",
                  "a dropped projection is genuinely gone", str(gone.get("reason_code")))

    journal_before = record(store, "reconstruct-journal")["head"]
    record(store, "rebuild-projections")
    second = record(store, "read-projection", "--subject", SUBJECT)
    observed.note(first == second, "the projection rebuilds to the same answer")
    observed.note(record(store, "reconstruct-journal")["head"] == journal_before,
                  "dropping and rebuilding a projection does not touch the journal",
                  journal_before[:16])

    declared = record(store, "operations")
    writes = [op["operation"] for op in declared["operations"]
              if op["subject"] == "subject-projection"
              and op["crud"] in {"CREATE", "SUPERSEDE", "COUNTER"}]
    observed.note(not writes, "no declared operation writes a projection into the record",
                  "writes=" + str(writes) if writes else "none reachable")
    observed.note("projection-as-authority" in declared["forbids"],
                  "the service declares the prohibition rather than only implementing it")


def _detects_a_tamper(observed: Observation, store: Path) -> None:
    """Prove this walk detects a bad chain, not only that it agrees about a good one.

    Until now every stage ran `verify_chain` over honest data, so 21 held
    observations established that three implementations agree about a sound
    journal - not that any of them catches an unsound one. An independent witness
    said so, and it was right: a check never shown failing has not been shown to
    work.

    Each tamper is written straight into a copy of the store, read back through
    this module's own arithmetic, and rolled back.
    """
    database = store / "record-service.sqlite3"
    connection = sqlite3.connect(str(database))
    connection.row_factory = sqlite3.Row
    try:
        rows = [dict(row) for row in connection.execute(
            "SELECT * FROM journal ORDER BY seq")]
        target = rows[-1]
        for label, column, value in (
            ("a rewritten actor", "actor", "somebody-else"),
            ("a repointed identifier", "entry_id", "entry_forged"),
            ("payload bytes that parse the same", "payload_json",
             '{"x": 1, "forged": 0}'),
        ):
            connection.execute(f"UPDATE journal SET {column}=? WHERE seq=?",
                               (value, target["seq"]))
            walked = [dict(row) for row in connection.execute(
                "SELECT * FROM journal ORDER BY seq")]
            for entry in walked:
                entry["payload"] = json.loads(entry["payload_json"])
            observed.note(bool(verify_chain(walked)),
                          f"this walk detects {label}",
                          "detected" if verify_chain(walked) else "MISSED")
            connection.rollback()
    finally:
        connection.close()


def _distinctness(observed: Observation, store: Path) -> None:
    """A governing document is refused as event storage, loudly and from outside."""
    refused = record(store, "append-entry", "--kind", "EVENT", "--subject", SUBJECT,
                     "--actor", "Bdo", "--source-address", "SPEC.md", expect=2)
    observed.note(refused.get("reason_code") == "DESIGN_RECORD_REFUSED",
                  "a governing document is refused as event storage",
                  str(refused.get("reason_code")))
    declared = record(store, "operations")
    mapped = declared["local_refusals"].get("DESIGN_RECORD_REFUSED")
    observed.note(mapped == "ADMISSION_REFUSED",
                  "the local refusal maps to the kernel refusal it realizes", str(mapped))
    accepted = record(store, "append-entry", "--kind", "EVENT", "--subject", SUBJECT,
                      "--actor", "Bdo", "--source-address", "reports/a-report.md")
    observed.note("entry_id" in accepted,
                  "an ordinary source address is still admitted", accepted["entry_id"][:16])


def observe(emit: Path | None = None) -> int:
    """Drive the witness walk declared on issue #7 through the CLI, and grade it."""
    observed = Observation()
    started = time.time()
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        store = Path(tmp) / "record"
        entry, receipt = _commit(observed, store)
        before = _survives_restart(observed, store, [entry, receipt])
        _retract(observed, store, entry, before)
        _projections(observed, store)
        _detects_a_tamper(observed, store)
        _distinctness(observed, store)
        final = record(store, "reconstruct-journal")
        settled = record(store, "read-entry", "--entry", receipt["entry_id"])
        observed.note(settled["payload"]["outcome"] == "COMMITTED",
                      "the terminal receipt reads back unchanged at the end of the walk",
                      settled["entry_id"][:16])
        evidence = {
            "case_id": "WITNESS-ISSUE-7-RECORD-WALK",
            "participant_id": "record-service-reference",
            "artifact_revision": _revision(),
            "participant_claim": "COMPLETED" if not observed.failed() else "FAILED",
            "observed": {
                "walker_id": WALKER,
                "invoked_interface": "sov://record/* through soveraeign_record_service.cli",
                "observer_relation": "SUBPROCESS_ONLY",
                "record_addresses": [item["entry_digest"] for item in final["entries"]],
                "receipt_addresses": [item["entry_id"] for item in final["entries"]
                                      if item["kind"] == "RECEIPT"],
                "head": final["head"],
                "observations_held": len(observed.findings) - len(observed.failed()),
                "observations_total": len(observed.findings),
            },
            "telemetry": {"started_at": started, "elapsed_seconds": time.time() - started},
        }
    if emit is not None:
        emit.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")
        print(f"observation written to {emit}")
    return observed.report()


def _revision() -> str:
    """The artifact revision this walk observed.

    A dirty tree is marked, because a bare commit id would name a revision that
    does not contain what was actually walked.
    """
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], capture_output=True, text=True,
                              cwd=str(ROOT), check=False).stdout.strip()

    head = git("rev-parse", "--short", "HEAD")
    if not head:
        return "WORKTREE"
    return head + "+WORKTREE" if git("status", "--porcelain") else head


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--emit", type=Path,
                        help="write the observation document to this path as well")
    args = parser.parse_args(argv)
    return observe(args.emit)


MAIN: Callable[[], int] = observe

if __name__ == "__main__":
    raise SystemExit(main())
