"""Independent probe of the Record Service append-preserving claim.

Witness-owned. It does not import the Record Service. It reaches the service
only as a subprocess through the declared CLI surface
(`services/record/contracts/service.json`), and it recomputes the digest chain
from the rule stated in `services/record/CHARTER.md` rather than from
`core.py`, so a chain that only verifies against its own implementation shows
up as a disagreement rather than as a pass.

Every check is written to try to defeat the claim, not to confirm it. Run:

    python witness/probes/probe_record_journal.py

It writes a JSON report to stdout and exits 0 whether or not the subject
survives; deciding what the result earns is the reader's job, not this file's.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "services" / "record" / "src"
GENESIS = "0" * 64


class ProbeError(RuntimeError):
    """The probe could not reach the subject at all."""


def cli(root: Path, *argv: str) -> tuple[int, Any]:
    """Drive the declared CLI as a subprocess and return (exit code, payload)."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC)
    done = subprocess.run(
        [sys.executable, "-m", "soveraeign_record_service.cli", "--root", str(root), *argv],
        capture_output=True, text=True, env=env, cwd=str(REPO), timeout=120,
    )
    try:
        return done.returncode, json.loads(done.stdout)
    except json.JSONDecodeError:
        return done.returncode, (done.stdout + done.stderr).strip()


def reason_of(result: Any) -> str | None:
    """Pull a refusal reason code out of a CLI payload, when there is one."""
    return result.get("reason_code") if isinstance(result, dict) else None


def charter_digest(prev: str, kind: str, subject: str, actor: str, payload: Any) -> str:
    """Recompute one link from the rule CHARTER.md states, not from core.py.

    "Every entry's digest is sha256 over prev_digest, kind, subject, actor, and
    the entry payload as canonical JSON, joined by |."
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    joined = "|".join([prev, kind, subject, actor, canonical])
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def store_files(root: Path) -> list[Path]:
    """List every file under the store root, without asking the service."""
    return sorted(path for path in root.rglob("*") if path.is_file())


def open_store(root: Path) -> sqlite3.Connection:
    """Open whichever file under the store root is a SQLite database."""
    for candidate in store_files(root):
        try:
            connection = sqlite3.connect(candidate)
            connection.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
            return connection
        except sqlite3.DatabaseError:
            continue
    raise ProbeError(f"no SQLite store under {root}")


def locate(connection: sqlite3.Connection, column: str) -> tuple[str | None, list[str]]:
    """Find the table carrying a named column, without asking the service.

    The match is by prefix because the stored column name need not equal the
    logical field name; the journal stores `payload` as `payload_json`.
    """
    tables = [row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")]
    for table in tables:
        if table.startswith("sqlite_"):
            continue
        columns = [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
        if any(name == column or name.startswith(f"{column}_") for name in columns):
            return table, columns
    return None, tables


def payload_column(columns: list[str]) -> str:
    """Name the stored payload column among a table's columns."""
    return next(name for name in columns if name == "payload" or name.startswith("payload_"))


def seed(root: Path, count: int = 4) -> list[dict[str, Any]]:
    """Write a small journal through the declared surface."""
    written = []
    for index in range(1, count + 1):
        code, payload = cli(root, "append-entry", "--kind", "EVENT",
                            "--subject", f"probe/subject-{index}",
                            "--actor", f"witness:probe-{index}",
                            "--payload", json.dumps({"n": index, "note": f"entry {index}"}))
        if code != 0:
            raise ProbeError(f"seed append refused: {payload}")
        written.append(payload)
    return written


def check_chain_rule_is_the_declared_one(root: Path, _: Path) -> dict[str, Any]:
    """RED: does the documented rule actually reproduce the stored digests?

    If it does not, an outside observer cannot verify this journal from the
    documentation, which is the reachability the charter claims for it.
    """
    seeded = seed(root)
    code, replay = cli(root, "reconstruct-journal")
    if code != 0:
        return {"held": False, "why": f"reconstruct refused on a clean journal: {replay}"}
    prev = GENESIS
    mismatches = []
    for entry in replay["entries"]:
        mine = charter_digest(prev, entry["kind"], entry["subject"], entry["actor"],
                              entry["payload"])
        if mine != entry["entry_digest"]:
            mismatches.append({"entry_id": entry["entry_id"], "stored": entry["entry_digest"],
                               "recomputed_from_charter": mine})
        prev = entry["entry_digest"]
    return {"held": not mismatches, "entries": len(replay["entries"]),
            "seeded": len(seeded), "head": replay["head"], "mismatches": mismatches,
            "attack": "recompute every digest from CHARTER.md's stated rule alone"}


def check_no_mutation_on_the_reachable_surface(root: Path, _: Path) -> dict[str, Any]:
    """RED: is there any declared operation that edits or deletes an entry?"""
    code, ops = cli(root, "operations")
    if code != 0:
        return {"held": False, "why": f"discovery refused: {ops}"}
    offending = [op["operation"] for op in ops["operations"]
                 if op.get("subject") in {"journal-entry", "terminal-receipt", "counter-record",
                                          "digest-chain"}
                 and op.get("crud") in {"UPDATE", "DELETE"}]
    return {"held": not offending, "declared_operations": len(ops["operations"]),
            "mutating_operations": offending,
            "attack": "read the declared surface for any entry UPDATE or DELETE"}


def check_payload_rewrite_is_caught(root: Path, _: Path) -> dict[str, Any]:
    """RED: edit a committed payload behind the CLI's back. Does replay refuse?"""
    seed(root)
    connection = open_store(root)
    with connection:
        table, columns = locate(connection, "payload")
        if table is None:
            return {"held": None, "why": f"no payload column found; tables were {columns}"}
        column = payload_column(columns)
        row = connection.execute(
            f"SELECT rowid FROM {table} ORDER BY rowid LIMIT 1").fetchone()
        connection.execute(f"UPDATE {table} SET {column} = ? WHERE rowid = ?",
                           (json.dumps({"n": 999, "note": "rewritten by the probe"}), row[0]))
    connection.close()
    code, result = cli(root, "reconstruct-journal")
    return {"held": code != 0, "exit_code": code, "reason_code": reason_of(result),
            "attack": "UPDATE the first entry's stored payload directly in SQLite"}


def check_entry_removal_is_caught(root: Path, _: Path) -> dict[str, Any]:
    """RED: cut an entry out of the middle. Does replay refuse?"""
    seed(root)
    connection = open_store(root)
    with connection:
        table, columns = locate(connection, "payload")
        if table is None:
            return {"held": None, "why": f"no journal table found; tables were {columns}"}
        rows = connection.execute(f"SELECT rowid FROM {table} ORDER BY rowid").fetchall()
        if len(rows) < 3:
            return {"held": None, "why": "too few rows to cut a middle entry"}
        connection.execute(f"DELETE FROM {table} WHERE rowid = ?", (rows[1][0],))
    connection.close()
    code, result = cli(root, "reconstruct-journal")
    return {"held": code != 0, "exit_code": code, "reason_code": reason_of(result),
            "attack": "DELETE the second journal row directly in SQLite"}


def check_undigested_fields(root: Path, _: Path) -> dict[str, Any]:
    """RED: rewrite a stored field the declared digest rule does not cover.

    The charter's rule binds prev_digest, kind, subject, actor and payload. Any
    other stored column is outside the chain, so editing it cannot break a link.
    This measures how much of an entry the append-preserving claim covers, which
    is a different question from whether the chain itself works.
    """
    seed(root)
    connection = open_store(root)
    findings = []
    with connection:
        table, columns = locate(connection, "payload")
        if table is None:
            return {"held": None, "why": f"no journal table found; tables were {columns}"}
        digested = {payload_column(columns), "kind", "subject", "actor", "prev_digest"}
        structural = {"entry_digest", "seq", "id", "rowid"}
        outside = [name for name in columns if name not in digested and name not in structural]
        row = connection.execute(f"SELECT rowid FROM {table} ORDER BY rowid LIMIT 1").fetchone()
        for name in outside:
            connection.execute(f"UPDATE {table} SET {name} = ? WHERE rowid = ?",
                               ("PROBE-REWROTE-THIS", row[0]))
            findings.append(name)
    connection.close()
    code, result = cli(root, "reconstruct-journal")
    return {"detected": code != 0, "exit_code": code, "reason_code": reason_of(result),
            "columns_in_table": columns, "columns_rewritten": findings,
            "note": "detected=false means these fields sit outside the digest chain",
            "attack": "rewrite every stored column the declared digest rule omits"}


def check_retraction_preserves(root: Path, _: Path) -> dict[str, Any]:
    """RED: after a counter-record, is the original still readable and intact?"""
    written = seed(root, 2)
    original = written[0]
    code, countered = cli(root, "counter-entry", "--entry", original["entry_id"],
                          "--actor", "witness:probe", "--reason", "probe retraction")
    if code != 0:
        return {"held": False, "why": f"counter refused: {countered}"}
    code, reread = cli(root, "read-entry", "--entry", original["entry_id"])
    if code != 0:
        return {"held": False, "why": f"original unreadable after retraction: {reread}"}
    same_payload = reread.get("payload") == original["payload"]
    same_digest = reread.get("entry_digest") == original["entry_digest"]
    code, replay = cli(root, "reconstruct-journal")
    return {"held": bool(same_payload and same_digest and code == 0),
            "payload_intact": same_payload, "digest_intact": same_digest,
            "chain_still_verifies": code == 0,
            "entries_after_retraction": replay.get("count") if isinstance(replay, dict) else None,
            "counter_entry_id": countered.get("entry_id"),
            "attack": "counter an entry, then reread the original and replay the chain"}


def check_projection_is_rebuildable(root: Path, _: Path) -> dict[str, Any]:
    """RED: drop every projection and rebuild. Same answer, journal untouched?"""
    seed(root)
    code, before_head = cli(root, "reconstruct-journal")
    if code != 0:
        return {"held": False, "why": f"reconstruct refused: {before_head}"}
    # Appending does not materialize a projection; the manifest's declared
    # precondition for read-projection is `projection_built`, so build it first.
    unbuilt_code, unbuilt = cli(root, "read-projection", "--subject", "probe/subject-1")
    cli(root, "rebuild-projections")
    code, before = cli(root, "read-projection", "--subject", "probe/subject-1")
    if code != 0:
        return {"held": False, "why": f"projection unreadable after first build: {before}"}
    cli(root, "drop-projections")
    dropped_code, dropped = cli(root, "read-projection", "--subject", "probe/subject-1")
    cli(root, "rebuild-projections")
    code, after = cli(root, "read-projection", "--subject", "probe/subject-1")
    if code != 0:
        return {"held": False, "why": f"projection unreadable after rebuild: {after}"}
    code, after_head = cli(root, "reconstruct-journal")
    identical = before == after
    unchanged = before_head["head"] == after_head["head"]
    return {"held": bool(identical and unchanged), "projection_identical": identical,
            "head_unchanged": unchanged,
            "projection_declares_non_authoritative": before.get("authoritative") is False,
            "read_after_drop_exit_code": dropped_code,
            "read_after_drop_reason": reason_of(dropped),
            "read_before_any_build_exit_code": unbuilt_code,
            "read_before_any_build_reason": reason_of(unbuilt),
            "attack": "drop every projection, rebuild from the journal alone, compare"}


def check_design_record_refused(root: Path, _: Path) -> dict[str, Any]:
    """RED: try to journal a governing document as a source. Refused?"""
    seed(root, 1)
    attempts = {}
    for name in ("SPEC.md", "CONTRACT.md", "STATUS.yaml", "AGENTS.md"):
        code, result = cli(root, "append-entry", "--kind", "EVENT", "--subject", "probe/design",
                           "--actor", "witness:probe", "--payload", "{}",
                           "--source-address", name)
        attempts[name] = {"exit_code": code, "reason_code": reason_of(result)}
    return {"held": all(a["exit_code"] != 0 for a in attempts.values()), "attempts": attempts,
            "attack": "append an entry sourced from a governing document"}


def check_truncation(root: Path, work: Path) -> dict[str, Any]:
    """RED: cut the tail off an export. Is the charter's own admission accurate?

    The charter says truncation cannot be caught from inside the document, and
    that only an externally held head catches it. Both halves are tested; a
    charter overstating its guarantee would fail the first half.
    """
    seed(root, 4)
    work.mkdir(parents=True, exist_ok=True)
    export = work / "export.json"
    code, written = cli(root, "export-journal", "--out", str(export))
    if code != 0:
        return {"held": None, "why": f"export refused: {written}"}
    document = json.loads(export.read_text(encoding="utf-8"))
    entries = document.get("entries", [])
    if len(entries) < 3:
        return {"held": None, "why": f"export too short to truncate: {sorted(document)}"}
    code, replay = cli(root, "reconstruct-journal")
    true_head = replay["head"] if code == 0 else ""
    kept = entries[:-1]
    document["entries"] = kept
    # A truncation is only a real attack if every self-declared field is made
    # consistent with the shorter document. Leaving a stale count behind would
    # be caught by arithmetic rather than by the chain, and would understate
    # what an attacker can do.
    rewritten: list[str] = []
    for key in list(document):
        if key == "entries":
            continue
        value = document[key]
        if isinstance(value, str) and value == true_head:
            document[key] = kept[-1]["entry_digest"]
            rewritten.append(key)
        elif isinstance(value, int) and not isinstance(value, bool) and value == len(entries):
            document[key] = len(kept)
            rewritten.append(key)
    truncated = work / "truncated.json"
    truncated.write_text(json.dumps(document, indent=2), encoding="utf-8")
    inside_code, inside = cli(root, "verify-export", "--export", str(truncated))
    outside_code, outside = cli(root, "verify-export", "--export", str(truncated),
                                "--expect-head", true_head)
    return {"undetected_without_external_head": inside_code == 0,
            "detected_with_external_head": outside_code != 0,
            "charter_admission_accurate": inside_code == 0 and outside_code != 0,
            "self_declared_fields_rewritten": rewritten,
            "entries_kept": len(kept), "entries_originally": len(entries),
            "inside": {"exit_code": inside_code, "reason_code": reason_of(inside)},
            "outside": {"exit_code": outside_code, "reason_code": reason_of(outside)},
            "attack": "drop the last export entry, then rewrite every self-declared "
                      "field so the shorter document is internally consistent"}


def check_restore_into_non_empty(root: Path, work: Path) -> dict[str, Any]:
    """RED: replay an export into a store that already holds a journal."""
    seed(root, 2)
    work.mkdir(parents=True, exist_ok=True)
    export = work / "restore-source.json"
    code, written = cli(root, "export-journal", "--out", str(export))
    if code != 0:
        return {"held": None, "why": f"export refused: {written}"}
    code, result = cli(root, "restore-journal", "--export", str(export))
    return {"held": code != 0, "exit_code": code, "reason_code": reason_of(result),
            "attack": "restore an export into a store that already holds entries"}


def check_export_of_a_broken_journal(root: Path, work: Path) -> dict[str, Any]:
    """RED: break the chain, then ask for an export. Refused, or copied anyway?"""
    seed(root)
    connection = open_store(root)
    with connection:
        table, columns = locate(connection, "payload")
        if table is None:
            return {"held": None, "why": f"no journal table found; tables were {columns}"}
        column = payload_column(columns)
        row = connection.execute(f"SELECT rowid FROM {table} ORDER BY rowid LIMIT 1").fetchone()
        connection.execute(f"UPDATE {table} SET {column} = ? WHERE rowid = ?",
                           (json.dumps({"broken": True}), row[0]))
    connection.close()
    work.mkdir(parents=True, exist_ok=True)
    export = work / "broken-export.json"
    code, result = cli(root, "export-journal", "--out", str(export))
    return {"held": code != 0, "exit_code": code, "reason_code": reason_of(result),
            "export_written_anyway": export.exists(),
            "attack": "rewrite a payload, then export the journal that no longer verifies"}


def check_history_can_be_quietly_rewritten(root: Path, _: Path) -> dict[str, Any]:
    """RED: rewrite the story the journal tells, without breaking a single link.

    The charter says a rewritten history "stops verifying rather than quietly
    replacing the real one". That holds for the five fields the digest covers.
    This check asks what happens to the fields it does not cover: it inverts
    every entry's recorded time and rewrites every source address, then replays.
    A journal that still verifies, with an unchanged head, is one whose chain is
    sound and whose coverage is narrower than the sentence claims.
    """
    seed(root, 4)
    code, before = cli(root, "reconstruct-journal")
    if code != 0:
        return {"held": None, "why": f"reconstruct refused on a clean journal: {before}"}
    times = [entry.get("recorded_at") for entry in before["entries"]]
    connection = open_store(root)
    with connection:
        table, columns = locate(connection, "payload")
        if table is None or "recorded_at" not in columns:
            return {"held": None, "why": f"no recorded_at column; columns were {columns}"}
        rows = [row[0] for row in connection.execute(
            f"SELECT rowid FROM {table} ORDER BY rowid")]
        for rowid, stamp in zip(rows, reversed(times)):
            connection.execute(
                f"UPDATE {table} SET recorded_at = ?, source_address = ? WHERE rowid = ?",
                (stamp, "lineage/evidence/fabricated-by-the-probe", rowid))
    connection.close()
    code, after = cli(root, "reconstruct-journal")
    if code != 0:
        return {"history_rewritten_undetected": False, "exit_code": code,
                "reason_code": reason_of(after)}
    now = [entry.get("recorded_at") for entry in after["entries"]]
    sources = {entry.get("source_address") for entry in after["entries"]}
    return {"history_rewritten_undetected": True,
            "replay_exit_code": code,
            "head_unchanged": before["head"] == after["head"],
            "recorded_at_before": times, "recorded_at_after": now,
            "timestamps_changed": times != now,
            "source_addresses_after": sorted(str(s) for s in sources),
            "attack": "invert every entry's recorded time and rewrite every source "
                      "address in SQLite, then replay the chain"}


PLAN = [
    ("chain_rule_is_the_declared_one", check_chain_rule_is_the_declared_one),
    ("no_mutation_on_the_reachable_surface", check_no_mutation_on_the_reachable_surface),
    ("payload_rewrite_is_caught", check_payload_rewrite_is_caught),
    ("entry_removal_is_caught", check_entry_removal_is_caught),
    ("undigested_fields", check_undigested_fields),
    ("history_can_be_quietly_rewritten", check_history_can_be_quietly_rewritten),
    ("retraction_preserves_the_original", check_retraction_preserves),
    ("projection_is_rebuildable", check_projection_is_rebuildable),
    ("design_record_refused", check_design_record_refused),
    ("truncation", check_truncation),
    ("restore_into_non_empty_refused", check_restore_into_non_empty),
    ("export_of_a_broken_journal_refused", check_export_of_a_broken_journal),
]


def main() -> int:
    """Run every check against its own fresh store and report what each returned."""
    work = Path(tempfile.mkdtemp(prefix="witness-record-"))
    report: dict[str, Any] = {"probe": "witness/probes/probe_record_journal.py",
                              "subject": "services/record",
                              "reached_through": "soveraeign_record_service.cli as a subprocess",
                              "checks": {}}
    for name, function in PLAN:
        root = work / name / "store"
        root.mkdir(parents=True, exist_ok=True)
        try:
            report["checks"][name] = function(root, work / name / "files")
        except Exception as failure:  # a probe that dies is a result, not a crash
            report["checks"][name] = {"held": None, "probe_error": repr(failure)}
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
