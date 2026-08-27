"""Who was graded, and who graded them.

Split from `refusals.py` at the line ceiling, along the boundary the refusals already had:
the rest of that module asks whether a record is arithmetically honest about itself, and
this asks whether the two files it cites are real and were made by somebody else.

Both questions here were defeated repeatedly. The answers digest was recorded and never
checked; then checked but switched off by omitting the path. The verdict file was a path
nobody opened; then opened but verified outside the repository. Each repair went into the
producer and had to be put into the reader as well, because `records.load_all` grades every
record on disk and a hand-placed one never went through a producer.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any
import json

from sovcoldstart.source import ROOT, digest_of
from sovcoldstart.tiers import _numbers

def _competence_defects(record: dict[str, Any]) -> list[dict[str, str]]:
    """What a participant reading has to carry beyond a tier table."""
    out = []
    participant = record.get("participant")
    if not isinstance(participant, dict) or not participant:
        # `participant: "me"` used to raise AttributeError here rather than refuse, and
        # `load_all` grades every file on disk, so one such record broke `history` entirely.
        out.append({"code": "PARTICIPANT_MISSING",
                    "detail": "a competence score with no participant object is a number "
                              "about nobody"})
    elif not participant.get("answers"):
        # The digest was required and the path was not, so omitting the path switched the
        # check off and left a digest of nothing, bound to nothing.
        out.append({"code": "ANSWERS_UNVERIFIED",
                    "detail": "participant states a digest and no answers path, so the "
                              "digest identifies nothing"})
    else:
        # The digest was recorded and never checked, so it identified nothing. A digest of
        # a file that is not there identifies nothing either.
        out.extend(_file_defects("ANSWERS_UNVERIFIED", "participant.answers",
                                 participant["answers"], participant.get("answers_digest")))
        out.extend(_answers_shape(participant["answers"], record))
    graded = record.get("graded_by")
    if not isinstance(graded, dict):
        out.append({"code": "SELF_GRADED",
                    "detail": "a competence run states no graded_by block, so nothing says "
                              "who graded the answers a string comparison cannot judge"})
        return out
    asked, done = graded.get("manual_asked"), graded.get("manual_graded")
    if isinstance(asked, int) and isinstance(done, int) and done > asked:
        out.append({"code": "COUNTS_DISAGREE",
                    "detail": f"graded_by grades {done} hand-graded answers out of {asked} "
                              f"asked"})
    counted = _manual_in_corpus(record)
    if counted is not None and asked != counted:
        # Read from the corpus rather than from the record. Declaring nothing hand-graded
        # and nothing hand-asked skipped every check below it, and the corpus this record
        # binds by digest says how many prose questions it contains.
        out.append({"code": "COUNTS_DISAGREE",
                    "detail": f"graded_by states {asked} hand-graded question(s) asked and "
                              f"the corpus it names contains {counted}"})
        asked = counted
    ungraded = (asked - done) if isinstance(asked, int) and isinstance(done, int) else 0
    if ungraded:
        unmeasured = sum(row["unmeasured"] for row in _numbers(record.get("tiers")))
        if unmeasured < ungraded:
            # Saying nothing was hand-graded used to switch SELF_GRADED off entirely. The
            # record already carries the contradiction: a question nobody graded is a
            # question nothing measured.
            out.append({"code": "COUNTS_DISAGREE",
                        "detail": f"graded_by leaves {ungraded} hand-graded answer(s) "
                                  f"ungraded and the tier table records only {unmeasured} "
                                  f"unmeasured"})
    if not done:
        return out
    verdicts = graded.get("owner_verdicts")
    if not verdicts or not str(verdicts).strip():
        out.append({"code": "SELF_GRADED",
                    "detail": f"{done} hand-graded answer(s) scored with no owner verdict "
                              f"file; no seat settles its own output"})
        return out
    # The path was recorded and never opened, so any non-empty string satisfied the rule
    # that no seat settles its own output. The check that already exists for `answers`
    # seventeen lines above is the one this field needed.
    out.extend(_file_defects("SELF_GRADED", "graded_by.owner_verdicts", verdicts,
                             graded.get("owner_verdicts_digest")))
    file = inside(verdicts)
    if file is None or not file.is_file():
        return out
    try:
        doc = json.loads(file.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        out.append({"code": "SELF_GRADED",
                    "detail": f"{verdicts} cannot be read as a verdict file: {exc}"})
        return out
    stated = participant.get("answers_digest") if isinstance(participant, dict) else None
    if doc.get("grades_answer_digest") != stated:
        out.append({"code": "SELF_GRADED",
                    "detail": f"{verdicts} grades answers digesting to "
                              f"{doc.get('grades_answer_digest')}, and this record grades "
                              f"answers digesting to {stated}"})
    out.extend(_grader_defects(doc.get("graded_by"), verdicts))
    return out


def _answers_shape(rel: Any, record: dict[str, Any]) -> list[dict[str, str]]:
    """The cited file has to be a submission. A witness cited README.md and it was admitted.

    Existing and digesting correctly says a file was not swapped. It says nothing about the
    file being the thing the record claims was graded.
    """
    path = inside(rel)
    if path is None or not path.is_file():
        return []
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return [{"code": "ANSWERS_UNVERIFIED",
                 "detail": f"participant.answers names {rel!r}, which is not JSON"}]
    answers = doc.get("answers") if isinstance(doc, dict) else None
    if not isinstance(answers, list) or not answers:
        return [{"code": "ANSWERS_UNVERIFIED",
                 "detail": f"participant.answers names {rel!r}, which carries no answers"}]
    if any(not isinstance(a, dict) or "id" not in a for a in answers):
        return [{"code": "ANSWERS_UNVERIFIED",
                 "detail": f"participant.answers names {rel!r}, whose answers do not carry "
                           f"question ids"}]
    # Shape alone said nothing about the file being what this record claims was graded.
    doc = canonical_corpus(record)
    if doc is None:
        return []
    known = {q.get("id") for q in doc.get("questions", [])}
    unknown = sorted({a["id"] for a in answers} - known)
    if unknown:
        return [{"code": "ANSWERS_UNVERIFIED",
                 "detail": f"participant.answers names {rel!r}, which answers question(s) "
                           f"{unknown[:5]} that are not in the corpus this record binds"}]
    selected = (record.get("corpus") or {}).get("selected")
    if isinstance(selected, int) and len(answers) > selected:
        return [{"code": "ANSWERS_UNVERIFIED",
                 "detail": f"participant.answers carries {len(answers)} answers and the "
                           f"record says {selected} questions were selected"}]
    return []


def _manual_in_corpus(record: dict[str, Any]) -> int | None:
    """How many hand-graded questions the bound corpus holds, or None if it cannot be read.

    Only when the corpus on disk still digests to what the record states: an older record
    names a corpus that has moved on, and counting today's questions against yesterday's
    reading would mark every past record defective. At write time the digest always matches,
    which is where a forged record would be born.
    """
    doc = canonical_corpus(record)
    if doc is None:
        return None
    return sum(1 for q in doc.get("questions", []) if q.get("grade") == "manual")


def canonical_corpus(record: dict[str, Any]) -> dict[str, Any] | None:
    """The pinned corpus, when this record is a reading of the version now on disk.

    The path comes from `CANONICAL_CORPUS`, never from the record: a witness pointed a
    record at a one-answer fixture with a true digest and every count derived from it came
    out flattering. The digest still has to match, because an older record names a corpus
    that has moved on and counting today's questions against yesterday's reading would mark
    every past record defective. At write time it always matches, which is where a forged
    record is born.
    """
    from sovcoldstart.refusals import CANONICAL_CORPUS

    path = ROOT / CANONICAL_CORPUS
    if not path.is_file():
        return None
    if digest_of(path) != (record.get("corpus") or {}).get("digest"):
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def _grader_defects(grader: Any, verdicts: str) -> list[dict[str, str]]:
    """Whether the seat that graded the prose is one that can.

    Digest-binding two files proves they were made together, which a participant does
    trivially: a witness wrote both, put the sha256 of its own answers in the verdict file,
    named itself the grader, and granted RIGHT to all 57 hand-graded questions. The refusal
    was named for a rule it did not enforce.

    `decisions/0070` already settled the shape of the answer for the AI-native grader: a
    judgement is refused unless a registered `HUMAN` principal made it. The same mechanism
    applies here, because it is the same rule - `AGENTS.md`, no seat settles its own output.
    The registry is a projection and grants nothing, so this is a floor rather than a proof:
    it stops a participant naming itself, and it does not stop someone with write access to
    `contracts/principals.json` from adding an entry.
    """
    if not isinstance(grader, str) or not grader.strip():
        return [{"code": "SELF_GRADED",
                 "detail": f"{verdicts} names no graded_by seat, so nothing says who made "
                           f"these verdicts"}]
    named = grader.strip().lower()
    try:
        registry = json.loads((ROOT / "contracts" / "principals.json")
                              .read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        return [{"code": "SELF_GRADED",
                 "detail": f"the principal registry cannot be read, so {grader!r} resolves "
                           f"to nothing: {exc}"}]
    # Whole identifiers on both sides. Taking the suffix after the last colon meant
    # `hostile-agent:bdo` and `x:bdo` both resolved to the registered human `principal:bdo`,
    # which is not a floor, it is a hole with a floor's name on it. A bare name is admitted
    # only as the exact tail of a registered id, never as the tail of something else.
    kinds: dict[str, Any] = {}
    for entry in registry.get("principals", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("principal_id"), str):
            continue
        full = entry["principal_id"].strip().lower()
        kinds[full] = entry.get("kind")
        prefix, _, tail = full.rpartition(":")
        if prefix == "principal" and tail:
            kinds[tail] = entry.get("kind")
    if named not in kinds:
        return [{"code": "SELF_GRADED",
                 "detail": f"{verdicts} was graded by {grader!r}, which is in no principal "
                           f"registry"}]
    if kinds[named] != "HUMAN":
        return [{"code": "SELF_GRADED",
                 "detail": f"{verdicts} was graded by {grader!r}, a {kinds[named]} "
                           f"principal; only a registered human settles a judgement claim"}]
    return []


def inside(rel: Any) -> Path | None:
    """The file this repository-relative path names, or None if it leaves the repository.

    `ROOT / rel` lets an absolute right-hand side win outright, and `..` walks out, so a
    record could cite a temp directory or a parent and have its digest verified there. The
    producer already refused both; the reader did not, and `load_all` grades every record
    on disk.
    """
    if not isinstance(rel, str) or not rel.strip():
        return None
    # Absoluteness and separators are platform-dependent, and a record is read on
    # nodes that are not the one that wrote it. "C:/Users/somebody/answers.json" is
    # absolute on Windows and a relative name on POSIX, so a single-flavour check
    # would resolve it inside the repository on Linux and verify a digest against a
    # file the record never meant. Refuse what either flavour calls absolute, and
    # read ".." under both separator conventions.
    for flavour in (PureWindowsPath, PurePosixPath):
        candidate = flavour(rel)
        if candidate.is_absolute() or ".." in candidate.parts:
            return None
    resolved = (ROOT / Path(rel)).resolve()
    return resolved if resolved.is_relative_to(ROOT) else None


def _file_defects(code: str, field: str, rel: Any, digest: Any) -> list[dict[str, str]]:
    """A recorded path and digest must name a file that is there and digests to that."""
    if not isinstance(rel, str) or not rel.strip():
        return [{"code": code, "detail": f"{field} is not a path"}]
    target = inside(rel)
    if target is None:
        return [{"code": code,
                 "detail": f"{field} names {rel!r}, which is outside the repository; a "
                           f"digest verified there means nothing to another reader"}]
    if not target.is_file():
        return [{"code": code,
                 "detail": f"{field} names {rel!r}, which is not a file; nothing about it "
                           f"can be checked"}]
    if digest is None:
        return [{"code": code,
                 "detail": f"{field} names a file and the record states no digest for it, "
                           f"so the reference identifies whatever that path holds today"}]
    if digest_of(target) != digest:
        return [{"code": code, "detail": f"{field}: {rel!r} does not digest to {digest}"}]
    return []
