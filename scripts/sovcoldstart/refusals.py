"""What a run record has to survive before anyone may read a verdict off it.

Split from `records.py` so that one module owns *making and reading* a record and this one
owns *refusing* it. They change for different reasons: the writer changes when a run
records something new, and this changes every time someone finds a field that was read
where it could have been checked. Four independent witness passes have now found sixteen
such fields between them - one on the first, seven on the second, eight on the third - so
the second reason fires far more often than the first, and the class should be assumed
alive until a pass finds none.

Eleven refusals. `conformance/fixtures/coldstart/run-cases.json` proves every one fires, and
`sov_coldstart.py selfcheck` fails if any of them has no case. Two more, `CORPUS_UNVERIFIED`
and `RECORD_WOULD_REPLACE`, fire only when a record is written and live in `records.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from sovcoldstart.attribution import _competence_defects, canonical_corpus
from sovcoldstart.tiers import _numbers
from sovcoldstart.report import derive, grade_row
from sovcoldstart.source import ROOT, digest_of, run_identity

SCHEMA = ROOT / "contracts" / "coldstart-run.schema.json"
TIERS = (0, 1, 2, 3)
#: The one corpus a run record may be a reading of. Fixed here rather than read out of the
#: record, which is the whole point: a witness bound `corpus.path` to a one-answer fixture
#: with a true digest, `_manual_in_corpus` counted zero hand-graded questions in it, and a
#: record claiming 175 of 175 ADMISSIBLE with no owner verdict anywhere was written and read
#: back clean. Every earlier repair had bound one more referent by digest and left the
#: record choosing which file the digest was of.
CANONICAL_CORPUS = "scripts/sovcoldstart/corpus.json"
REFUSALS = (
    "RECORD_SHAPE",
    "TIER_ARITHMETIC",
    "TIER_SET_INVALID",
    "TIER_NOT_DERIVED",
    "COUNTS_DISAGREE",
    "CORPUS_NOT_CANONICAL",
    "RUN_ID_NOT_DERIVED",
    "VERDICT_NOT_DERIVED",
    "STANDING_OVERCLAIMED",
    "PARTICIPANT_MISSING",
    "ANSWERS_UNVERIFIED",
    "SELF_GRADED",
)


def defects(record: Any, schema: dict[str, Any] | None = None) -> list[dict[str, str]]:
    """Every refusal this record earns, named. An empty list is an admissible record."""
    from sovkernel.jsonschema import validate

    found: list[dict[str, str]] = []
    if not isinstance(record, dict):
        return [{"code": "RECORD_SHAPE", "detail": "record is not an object"}]
    standing = record.get("standing")
    if standing != "BUILT":
        found.append({
            "code": "STANDING_OVERCLAIMED",
            "detail": f"standing {standing!r}; a benchmark run establishes BUILT and never more",
        })
    doc = schema if schema is not None else json.loads(SCHEMA.read_text(encoding="utf-8"))
    for message in validate(record, doc):
        found.append({"code": "RECORD_SHAPE", "detail": message})

    rows = _numbers(record.get("tiers"))
    seen: dict[int, dict[str, Any]] = {}
    for row in rows:
        tier = row.get("tier")
        if row["hit"] > row["scored"]:
            found.append({"code": "TIER_ARITHMETIC",
                          "detail": f"tier {tier}: hit {row['hit']} exceeds "
                                    f"scored {row['scored']}"})
        if row["scored"] + row["unmeasured"] != row["asked"]:
            found.append({"code": "TIER_ARITHMETIC",
                          "detail": f"tier {tier}: scored {row['scored']} plus "
                                    f"unmeasured {row['unmeasured']} is not asked "
                                    f"{row['asked']}"})
        if tier not in TIERS:
            continue
        # The tier set is fixed, so it is checked against the fixed set rather than
        # against whatever the record supplies. A witness deleted the tier 0 row and the
        # record derived ADMISSIBLE with no hard-invariant gate present at all, then
        # duplicated it so the clean copy came last and a visible FAIL read as DEGRADED.
        if tier in seen:
            found.append({"code": "TIER_SET_INVALID",
                          "detail": f"tier {tier} appears more than once; which row counts "
                                    f"would then be decided by their order"})
            continue
        seen[tier] = row
    missing = [tier for tier in TIERS if tier not in seen]
    if rows and missing:
        found.append({"code": "TIER_SET_INVALID",
                      "detail": f"no row for tier(s) {missing}; an absent tier is not a "
                                f"passed one and cannot be read as a clean one"})

    canonical = []
    for tier, row in sorted(seen.items()):
        want = grade_row(tier, row["asked"], row["scored"], row["hit"], row["unmeasured"])
        canonical.append(want)
        # The threshold and the per-tier result are computed from the counts, never read
        # out of the record. Both were readable before, and declaring `gate: 0.0` on two
        # tiers was enough to make an otherwise honest record derive ADMISSIBLE.
        if isinstance(row.get("gate"), bool):
            # True == 1.0 in Python, so a boolean slipped past both the enum and the
            # comparison below and landed in a numeric field.
            found.append({"code": "TIER_NOT_DERIVED",
                          "detail": f"tier {tier}: gate is a boolean, not a threshold"})
        for field in ("gate", "result"):
            if row.get(field) != want[field]:
                found.append({
                    "code": "TIER_NOT_DERIVED",
                    "detail": f"tier {tier}: record states {field} {row.get(field)!r}; "
                              f"{row['hit']}/{row['scored']} of {row['asked']} asked "
                              f"gives {want[field]!r}",
                })
    structural = {"TIER_ARITHMETIC", "TIER_SET_INVALID"}
    if len(canonical) == len(TIERS) and not any(d["code"] in structural for d in found):
        stated = record.get("verdict")
        computed, reason = derive(canonical)
        if stated != computed:
            found.append({
                "code": "VERDICT_NOT_DERIVED",
                "detail": f"record states {stated!r}; the tier table derives {computed!r} "
                          f"({reason})",
            })
        found.extend(_counts_disagree(record, canonical))

    corpus_path = (record.get("corpus") or {}).get("path")
    if corpus_path != CANONICAL_CORPUS:
        found.append({"code": "CORPUS_NOT_CANONICAL",
                      "detail": f"corpus.path is {corpus_path!r}; a run record is a reading "
                                f"of {CANONICAL_CORPUS} and of nothing else"})
    found.extend(_identity_defects(record))
    if record.get("mode") == "COMPETENCE":
        found.extend(_competence_defects(record))
    return found


def _identity_defects(record: dict[str, Any]) -> list[dict[str, str]]:
    """The run id derives from four fields the record already carries, so it is recomputed.

    It was written and never re-derived, and `write` names the file from it, so a record
    declaring an id it had not earned could take another record's filename. A witness
    dropped one carrying thirty-two f characters into a records directory and `history`
    read it clean.
    """
    corpus = record.get("corpus") or {}
    revision = record.get("revision") or {}
    participant = record.get("participant")
    who = participant.get("id", "") if isinstance(participant, dict) else ""
    want = run_identity(str(revision.get("commit")), str(corpus.get("digest")),
                        str(record.get("observed_at")), str(record.get("mode")), str(who))
    if record.get("run_id") != f"coldstart_{want}":
        return [{"code": "RUN_ID_NOT_DERIVED",
                 "detail": f"run_id {record.get('run_id')!r} is not what this record's "
                           f"commit, corpus digest, instant and mode derive"}]
    return []


def _counts_disagree(record: dict[str, Any], canonical: list[dict[str, Any]]) -> list[dict]:
    """The same run counted three ways must come out the same three times.

    `sections` drives the entire drift reading and `corpus.selected` says how much of the
    corpus was asked. Neither was reconciled with the tier table, so a record could claim
    999 of 999 in one block and 44 of 49 in another and be admitted.
    """
    out = []
    totals = {field: sum(row[field] for row in canonical)
              for field in ("asked", "scored", "hit", "unmeasured")}
    sections = record.get("sections")
    if not isinstance(sections, dict) or not sections:
        # An empty dict used to skip reconciliation entirely, which made omitting the block
        # the cheapest way past the check that the block agrees with anything.
        out.append({"code": "COUNTS_DISAGREE",
                    "detail": "the record states no sections, so the block the drift reading "
                              "is built from is reconciled against nothing"})
        return out
    for name, entry in sorted(sections.items()):
        if not isinstance(entry, dict):
            out.append({"code": "COUNTS_DISAGREE",
                        "detail": f"section {name!r} is not a set of counts"})
            continue
        # The same invariants the tier table already carried. Without them the totals could
        # reconcile while an individual section claimed 95 hits out of 45 scored, offset by
        # another claiming none, and `moved` reads the individual numbers.
        got = {field: entry.get(field) for field in ("asked", "scored", "hit", "unmeasured")}
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0
               for value in got.values()):
            out.append({"code": "COUNTS_DISAGREE",
                        "detail": f"section {name!r} carries a count that is not a "
                                  f"non-negative integer: {got}"})
        elif got["hit"] > got["scored"] or got["scored"] + got["unmeasured"] != got["asked"]:
            out.append({"code": "COUNTS_DISAGREE",
                        "detail": f"section {name!r} does not add up: {got}"})
    for field, total in totals.items():
        seen = sum(entry.get(field, 0) for entry in sections.values()
                   if isinstance(entry, dict) and isinstance(entry.get(field), int))
        if seen != total:
            out.append({"code": "COUNTS_DISAGREE",
                        "detail": f"sections total {seen} {field} and the tier table "
                                  f"totals {total}"})
    corpus = record.get("corpus") or {}
    selected, questions = corpus.get("selected"), corpus.get("questions")
    if isinstance(selected, int) and selected != totals["asked"]:
        out.append({"code": "COUNTS_DISAGREE",
                    "detail": f"corpus.selected is {selected} and the tier table asked "
                              f"{totals['asked']}"})
    if isinstance(selected, int) and isinstance(questions, int) and selected > questions:
        # `questions` was reconciled with nothing, so a record could select 175 out of 3.
        out.append({"code": "COUNTS_DISAGREE",
                    "detail": f"corpus.selected is {selected} out of {questions} questions"})
    doc = canonical_corpus(record)
    if doc is not None and questions != len(doc.get("questions", [])):
        out.append({"code": "COUNTS_DISAGREE",
                    "detail": f"corpus.questions is {questions} and the corpus this record "
                              f"binds holds {len(doc.get('questions', []))}"})
    return out
