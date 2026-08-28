"""The walk stage that proves the chain arithmetic detects a bad journal.

Separated from `witness_record.py` because it is the one stage that does not
drive the service. Every other stage reaches the participant as a subprocess
through its CLI; this one opens the SQLite file, writes a forgery straight into
it, and rolls back. That is a different relationship to the participant and it
earns its own module.

Why the stage exists at all: for twenty-one observations the walk ran
`verify_chain` only over honest data, which established that three
implementations agree about a sound journal - not that any of them catches an
unsound one. A check never shown failing has not been shown to work.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol
import json
import sqlite3

from sovwitness.record_chain import verify_chain


class Notes(Protocol):
    """The part of `sovwitness.Observation` this module uses."""

    def note(self, held: bool, claim: str, detail: str = ...) -> Any: ...


def same_parse_encoding(payload_json: str) -> str:
    """Different bytes for the same parsed value: spaced, key-sorted JSON.

    This is what makes the third tamper test the byte rule rather than the
    digest. Every profile binds the payload's parsed value, so bytes that parse
    identically leave the digest silent and the whole weight falls on the
    canonical-encoding requirement. A literal substituted here instead - bytes
    that parse to some *other* value - is caught by the digest, which is why the
    first version of this stage held even with the byte rule switched off.
    """
    return json.dumps(json.loads(payload_json), sort_keys=True, separators=(", ", ": "))


def detects_a_tamper(observed: Notes, store: Path) -> None:
    """Write three forgeries into a copy of the store and require each to be caught.

    Each is applied, read back through this module's own arithmetic, and rolled
    back, so the store is exactly as it was when the stage returns.
    """
    connection = sqlite3.connect(str(store / "record-service.sqlite3"))
    connection.row_factory = sqlite3.Row
    try:
        target = dict(list(connection.execute("SELECT * FROM journal ORDER BY seq"))[-1])
        spaced = same_parse_encoding(target["payload_json"])
        if spaced == target["payload_json"]:
            raise AssertionError(
                "the same-parse tamper equals the stored bytes; it would test nothing")
        for label, column, value in (
            ("a rewritten actor", "actor", "somebody-else"),
            ("a repointed identifier", "entry_id", "entry_forged"),
            ("payload bytes that parse the same", "payload_json", spaced),
        ):
            connection.execute(f"UPDATE journal SET {column}=? WHERE seq=?",
                               (value, target["seq"]))
            walked = [dict(row) for row in connection.execute(
                "SELECT * FROM journal ORDER BY seq")]
            for entry in walked:
                entry["payload"] = json.loads(entry["payload_json"])
            caught = bool(verify_chain(walked))
            observed.note(caught, f"this walk detects {label}",
                          "detected" if caught else "MISSED")
            connection.rollback()
    finally:
        connection.close()
