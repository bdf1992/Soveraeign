"""Build, refuse and read back one cold-start run record.

A benchmark that prints a card and exits leaves nothing to compare tomorrow against. This
module turns a run into a record under `reports/coldstart/`: which corpus, at which commit,
by which participant, and what each tier scored. Two records a day apart are then a
measurement of drift rather than two anecdotes.

The record carries a `verdict`, and `defects` recomputes it from the tier table. Every
other field in a record is a measurement; that one is a conclusion, and a participant that
writes its own conclusion has removed the only part of the reading anyone else was going to
check. `conformance/fixtures/coldstart/run-cases.json` proves each refusal fires.
"""

from __future__ import annotations

import pathlib
from pathlib import Path
from typing import Any
import json
from hashlib import sha256

from sovcoldstart.refusals import REFUSALS, SCHEMA, TIERS, defects  # noqa: F401
from sovcoldstart.report import derive, tally
from sovcoldstart.source import ROOT, _git, digest_of, run_identity  # noqa: F401

RECORDS = ROOT / "reports" / "coldstart"
CASES = ROOT / "conformance" / "fixtures" / "coldstart" / "run-cases.json"


def revision() -> dict[str, str]:
    """The commit every probe in this run read, and whether anything was uncommitted.

    DIRTY is recorded rather than refused. Most runs happen mid-change, and a card that
    refused to be taken until the tree was clean would never be taken at all; what matters
    is that a reader can tell which kind of reading they are holding.
    """
    dirty = bool(_git(["status", "--porcelain"]).strip())
    return {
        "commit": _git(["rev-parse", "HEAD"]).strip(),
        "branch": _git(["rev-parse", "--abbrev-ref", "HEAD"]).strip(),
        "tree_state": "DIRTY" if dirty else "CLEAN",
    }


def _sections(rows: list[dict[str, Any]], key: str, good: str,
              bad: tuple[str, ...]) -> dict[str, dict[str, int]]:
    """Per-section counts, so `history` can name which sections moved rather than that some did."""
    out: dict[str, dict[str, int]] = {}
    for row in rows:
        entry = out.setdefault(row["section"],
                               {"asked": 0, "scored": 0, "hit": 0, "unmeasured": 0})
        entry["asked"] += 1
        if row[key] == good:
            entry["hit"] += 1
            entry["scored"] += 1
        elif row[key] in bad:
            entry["scored"] += 1
        else:
            entry["unmeasured"] += 1
    return out


def _relative(path: pathlib.Path) -> str:
    """A corpus path a later reader can resolve. `--corpus <relative>` used to raise here."""
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT):
        raise SystemExit(f"{path} is outside the repository; a run record cites its corpus "
                         f"by repository-relative path")
    return resolved.relative_to(ROOT).as_posix()


def build(rows: list[dict[str, Any]], key: str, good: str, *, mode: str, observed_at: str,
          corpus: Path, questions: int, coverage: dict[str, Any],
          participant: dict[str, Any] | None = None,
          graded_by: dict[str, Any] | None = None, note: str | None = None) -> dict[str, Any]:
    """One run record. The verdict is derived here and re-derived by `defects`."""
    table = tally(rows, key, good)
    verdict, reason = derive(table)
    corpus_digest = digest_of(corpus)
    rev = revision()
    identity = run_identity(rev["commit"], corpus_digest, observed_at, mode,
                            (participant or {}).get("id", ""))
    record: dict[str, Any] = {
        "record_schema": "soveraeign-coldstart-run/v1",
        "run_id": f"coldstart_{identity}",
        "mode": mode,
        "observed_at": observed_at,
        "revision": rev,
        "corpus": {
            "path": _relative(corpus),
            "digest": corpus_digest,
            "questions": questions,
            "selected": len(rows),
        },
        "coverage": coverage,
        "tiers": table,
        "sections": _sections(rows, key, good, ("WRONG",) if key == "verdict" else ("DRIFT",)),
        "verdict": verdict,
        "standing": "BUILT",
        "note": note or reason,
    }
    if participant is not None:
        record["participant"] = participant
    if graded_by is not None:
        record["graded_by"] = graded_by
    return record


def fresh_defects(record: dict[str, Any]) -> list[dict[str, str]]:
    """What can be checked about a record only at the moment it is written.

    Just the corpus digest. `defects` grades a record against itself, which is all a reader
    of an old record can do: the corpus it names has moved on and re-digesting it today
    would mark every past reading defective.

    `RUN_ID_NOT_DERIVED` used to live here too and no longer does. A witness pointed out
    that the run id derives from four fields inside the record, so it needs nothing external
    and a hand-placed record with a forged id read clean through `history`. It is checked in
    `defects` now, where every reader applies it.
    """
    out: list[dict[str, str]] = []
    corpus = record.get("corpus") or {}
    path = ROOT / str(corpus.get("path", ""))
    if not path.is_file():
        out.append({"code": "CORPUS_UNVERIFIED",
                    "detail": f"corpus.path names {corpus.get('path')!r}, which is not a file"})
    elif digest_of(path) != corpus.get("digest"):
        out.append({"code": "CORPUS_UNVERIFIED",
                    "detail": f"corpus.digest does not match the bytes at "
                              f"{corpus.get('path')!r} at the moment of writing"})
    out.extend(_corpus_at_revision(record))
    return out


def _corpus_at_revision(record: dict[str, Any]) -> list[dict[str, str]]:
    """Is the corpus this record digests the corpus at the commit this record names?

    A peer session found four generated diagrams stamping a `source_digest` for `STATUS.yaml`
    that matches none of the thirty-four committed versions of that file: a builder had run
    in the shared tree and pinned whatever another session had in flight. A run record has
    exactly that shape and had exactly that hole. Two records already under
    `reports/coldstart/` name commit `cc95d85` and carry different corpus digests, which is
    only possible because the corpus was uncommitted and moving underneath them.

    `CORPUS_UNVERIFIED` compares the digest against the working tree, which proves the
    writer read what it says it read and proves nothing about whether anyone else can. This
    compares it against the commit, so a record is either reproducible from the repository
    or it is not written.

    Write time only, like `CORPUS_UNVERIFIED`. A reader of an old record must not re-run
    this: the commit may have been rebased away, and refusing a past reading on that ground
    is the same mistake as re-digesting a corpus that has since moved on.
    """
    from sovcoldstart.refusals import CANONICAL_CORPUS
    from sovcoldstart.source import ProbeError, _blob_at

    commit = str((record.get("revision") or {}).get("commit") or "")
    if not commit:
        return [{"code": "CORPUS_NOT_AT_REVISION",
                 "detail": "revision.commit is empty, so nothing says which tree this "
                           "record is a reading of"}]
    try:
        blob = _blob_at(commit, CANONICAL_CORPUS)
    except ProbeError as exc:
        return [{"code": "CORPUS_NOT_AT_REVISION",
                 "detail": f"{CANONICAL_CORPUS} is not reachable from {commit[:8]}, so this "
                           f"record digests bytes that exist only on this disk ({exc})"}]
    found = "sha256:" + sha256(blob).hexdigest()
    if found != (record.get("corpus") or {}).get("digest"):
        return [{"code": "CORPUS_NOT_AT_REVISION",
                 "detail": f"corpus.digest is not the digest of {CANONICAL_CORPUS} at "
                           f"{commit[:8]}, which is {found[:19]}...; the record pins a "
                           f"working-tree reading against a commit that does not hold it"}]
    return []


def write(record: dict[str, Any], root: Path | None = None) -> Path:
    """Write the record under `reports/coldstart/`, refusing to write a defective one.

    Never over a record that is already there. The filename is derived from the run id, and
    a record could declare an id it did not earn, so writing a second record over the first
    was a way to replace a NOT_ADMISSIBLE reading with an ADMISSIBLE one and leave no trace.
    `AGENTS.md`, State and execution: the record is append-preserving.
    """
    found = defects(record) + fresh_defects(record)
    if found:
        raise ValueError("; ".join(f"{d['code']}: {d['detail']}" for d in found))
    target = (root or RECORDS)
    target.mkdir(parents=True, exist_ok=True)
    name = (f"{record['observed_at'][:10]}-{record['mode'].lower()}-"
            f"{record['run_id'].split('_', 1)[1][:8]}.json")
    path = target / name
    body = (json.dumps(record, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    # Create-exclusive, then compare. Read-then-write left a window two writers both passed
    # through: a witness ran twelve trials on two threads and got one silent replacement and
    # two half-written files, and `load_all` raises on a torn file for the whole directory.
    try:
        with open(path, "xb") as handle:
            handle.write(body)
        return path
    except FileExistsError:
        pass
    if path.read_bytes() != body:
        raise ValueError(
            f"RECORD_WOULD_REPLACE: {path.name} already holds a different reading; a run "
            f"record is append-preserving and this one would overwrite it"
        )
    return path


def load_all(root: Path | None = None) -> list[dict[str, Any]]:
    """Every recorded run, oldest first. A record that no longer validates is kept and flagged."""
    target = root or RECORDS
    if not target.is_dir():
        return []
    out = []
    for path in sorted(target.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            # One unreadable file used to take the whole directory with it, so a single torn
            # write made `history` report nothing at all.
            out.append({"_path": path.name, "_defects": ["RECORD_SHAPE"], "mode": "?",
                        "verdict": "?", "observed_at": "", "run_id": "",
                        "tiers": [], "_unreadable": str(exc)})
            continue
        record["_path"] = (path.relative_to(ROOT).as_posix()
                           if path.is_relative_to(ROOT) else path.as_posix())
        record["_defects"] = [d["code"] for d in defects({k: v for k, v in record.items()
                                                          if not k.startswith("_")})]
        out.append(record)
    return sorted(out, key=lambda r: (r.get("observed_at", ""), r.get("run_id", "")))


def comparable(previous: dict[str, Any], current: dict[str, Any]) -> str | None:
    """Why these two runs cannot be compared, or None if they can.

    Two runs taken under different coverage are not a measurement of drift. A `--fast
    --offline` run and a full one differ in 35 probes, and every one of them reads as a
    section that moved, which is the opposite of the signal a daily cadence is for.
    """
    if previous.get("mode") != current.get("mode"):
        return f"different modes ({previous.get('mode')} then {current.get('mode')})"
    before, after = previous.get("coverage") or {}, current.get("coverage") or {}
    if before != after:
        return (f"different coverage (fast {before.get('fast')}/{after.get('fast')}, "
                f"offline {before.get('offline')}/{after.get('offline')}, "
                f"sections {before.get('sections')}/{after.get('sections')})")
    if (previous.get("corpus") or {}).get("digest") != (current.get("corpus") or {}).get("digest"):
        return "the corpus changed between the two runs"
    was, now = set(previous.get("sections") or {}), set(current.get("sections") or {})
    if was != now:
        # The flag as typed is not the same fact as the sections actually scored, and only
        # the second one is what `moved` diffs.
        return (f"different sections scored ({sorted(was - now) or 'none'} dropped, "
                f"{sorted(now - was) or 'none'} added)")
    return None


def moved(previous: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """Which sections scored differently between two runs, named rather than counted.

    This is what a daily cadence is for. `A section moved` is the signal to re-read that
    part of the orientation layer; a total that moved says only that something did.

    Callers must check `comparable` first: this function will happily diff two runs that
    measured different things.
    """
    before, after = previous.get("sections") or {}, current.get("sections") or {}
    lines = []
    for name in sorted(set(before) | set(after)):
        was, now = before.get(name, {}), after.get(name, {})
        if was.get("hit") != now.get("hit") or was.get("asked") != now.get("asked"):
            lines.append(f"{name}: {was.get('hit', 0)}/{was.get('asked', 0)} -> "
                         f"{now.get('hit', 0)}/{now.get('asked', 0)}")
    return lines
