"""The walk stages that grade which chain profile a store writes, and moving it.

Separated from `witness_record.py` for size, and because the second stage builds
its own store rather than using the walk's. That is not a convenience: the walk's
store is written by the current service, so it already carries the newest profile
and a forward adoption cannot happen in it. An earlier version of the first stage
exercised the report path and both refusals against that store and never reached
the operation, so replacing the whole success branch with garbage left the walk
green. An independent witness found that by mutation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Protocol
import sqlite3

from sovwitness.record_chain import (
    CANONICAL, GENESIS, LEGACY_DIGEST_PROFILE, recompute, verify_chain,
)

SUBJECT = "run-witness-1"


#: How this module reaches the participant: the walk's own subprocess runner,
#: passed in rather than imported. Importing it would make this module depend on
#: `witness_record`, which imports this one.
Runner = Callable[..., dict]


def _refusal(run: Runner, store: Path, *args: str) -> dict:
    """A refused call, graded rather than asserted.

    `record` raises `SystemExit` when the exit code is not the one expected, which
    ends the walk before it prints anything - so a mutation that turned a refusal
    into a success discarded every observation gathered up to that point, including
    the ones that had already caught it. A refusal that does not refuse is a
    finding, not a reason to stop looking.
    """
    try:
        return run(store, *args, expect=2)
    except SystemExit as ended:
        return {"reason_code": None, "did_not_refuse": str(ended).splitlines()[0]}


class Notes(Protocol):
    """The part of `sovwitness.Observation` this module uses."""

    def note(self, held: bool, claim: str, detail: str = ...) -> Any: ...


def profile_is_reachable(observed: Notes, store: Path, run: Runner) -> None:
    """Asking a store what it writes must be answerable from outside, and must not write.

    `adopt-profile` was declared and wired with no case of any kind: the service's
    own tests reach `adopt_profile` in Python, and nothing proved the declared
    operation was reachable, that reporting is free of effect, or that a refusal
    comes back as JSON rather than a traceback. It is checked here rather than in
    the service's tests because reachability is a claim about the declared path,
    which is what this walk exists to exercise.
    """
    # The forward move is graded first, deliberately. Run after the refusal
    # checks, a broken success branch makes the standing-still call exit 0 where 2
    # was expected, and the walk dies with a traceback instead of naming which
    # claim failed. A witness that only crashes has not observed anything.
    _adoption_moves_a_store(observed, store.parent / "adopting", run)
    before = run(store, "reconstruct-journal")
    reported = run(store, "adopt-profile")
    after = run(store, "reconstruct-journal")
    observed.note(reported.get("adopted") is False and bool(reported.get("writing_profile")),
                  "a store answers which chain profile it writes",
                  str(reported.get("writing_profile")))
    unchanged = after["head"] == before["head"] and after["count"] == before["count"]
    # The detail is computed from the outcome, not from `before`. Written the other
    # way it printed "head unmoved" on the failure where the head had moved, which
    # is a note that says the opposite of what it just measured.
    observed.note(unchanged, "asking which profile a store writes does not change it",
                  f"{before['count']} entries, head unmoved" if unchanged
                  else f"{before['count']} -> {after['count']} entries")
    standing_still = _refusal(run, store, "adopt-profile", "--to",
                              reported["writing_profile"], "--actor", "witness")
    observed.note(standing_still.get("reason_code") == "STALE_STATE",
                  "adopting the profile a store already writes is refused by name",
                  str(standing_still.get("reason_code")))
    unknown = _refusal(run, store, "adopt-profile", "--to",
                       "soveraeign-record-chain/v99", "--actor", "witness")
    observed.note(unknown.get("reason_code") == "MISSING_PRECONDITION",
                  "adopting a profile this service does not implement is refused by name",
                  str(unknown.get("reason_code")))


def _adoption_moves_a_store(observed: Notes, store: Path, run: Runner) -> None:
    """The forward move itself, against a store old enough to need it.

    This needs its own store and that is the whole point. The walk's store is
    written by the current service, so it already carries the newest profile and
    no forward adoption is possible through it - an earlier version of this stage
    exercised the report path and both refusals against that store and could never
    reach the operation, so replacing the entire success branch with garbage left
    the walk at 28/28. A fixture that makes the interesting branch unreachable by
    construction is the defect this concern keeps finding, and this one was mine.

    The store is built here by straight SQL, the way a service that predates the
    profile column wrote one.
    """
    store.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(store / "record-service.sqlite3")
    try:
        connection.execute(
            "CREATE TABLE journal(seq INTEGER PRIMARY KEY AUTOINCREMENT, entry_id TEXT NOT "
            "NULL UNIQUE, kind TEXT NOT NULL, subject TEXT NOT NULL, actor TEXT NOT NULL, "
            "source_address TEXT, payload_json TEXT NOT NULL, recorded_at REAL NOT NULL, "
            "prev_digest TEXT NOT NULL, entry_digest TEXT NOT NULL)")
        # Both the digest and the bytes come from this module's own arithmetic,
        # not from the participant. Seeding with the service's helpers would make
        # the walk's independence a fiction in the one stage that builds a store.
        seed = {"prev_digest": GENESIS, "kind": "EVENT", "subject": SUBJECT,
                "actor": "older-checkout", "payload": {"step": 0},
                "digest_profile": LEGACY_DIGEST_PROFILE}
        digest = recompute(GENESIS, seed)
        connection.execute(
            "INSERT INTO journal(entry_id,kind,subject,actor,source_address,payload_json,"
            "recorded_at,prev_digest,entry_digest) VALUES(?,?,?,?,?,?,?,?,?)",
            ("entry_before_profiles", "EVENT", SUBJECT, "older-checkout", None,
             CANONICAL[LEGACY_DIGEST_PROFILE](seed["payload"]), 1.0, GENESIS, digest))
        connection.commit()
    finally:
        connection.close()

    before = run(store, "adopt-profile")
    observed.note(before["writing_profile"].endswith("/v1"),
                  "a journal written before profiles existed reads as v1",
                  before["writing_profile"])
    moved = run(store, "adopt-profile", "--to", "soveraeign-record-chain/v3",
                   "--actor", "witness")
    observed.note(moved.get("adopted") is True
                  and moved.get("supersedes") == before["writing_profile"]
                  and moved.get("writing_profile", "").endswith("/v3"),
                  "adopting a newer profile moves the store and names what it supersedes",
                  f"{moved.get('supersedes')} -> {moved.get('writing_profile')}")
    replay = run(store, "reconstruct-journal")
    observed.note(len(replay["entries"]) == 2
                  and replay["entries"][-1]["entry_id"] == moved.get("entry_id"),
                  "the adoption is an entry in the journal, chained onto what was there",
                  str(len(replay["entries"])) + " entries")
    observed.note(bool(verify_chain(replay["entries"])) is False,
                  "the mixed-profile chain this walk just built verifies here too",
                  str(len(replay["entries"])) + " links")
