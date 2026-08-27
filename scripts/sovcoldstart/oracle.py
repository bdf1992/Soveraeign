"""The oracle: does the run-record contract still refuse what it declares?

Split from `verbs.py` at the line ceiling, along a boundary that was always there. The rest
of that module describes the surface - what it offers, what it asks, what it recorded. This
grades the contract against `conformance/fixtures/coldstart/run-cases.json` and fails when a
declared refusal has no case firing it.

Two things here are answers to findings rather than design. `_bind_canonical` substitutes
live digests into a case that asks for them by sentinel, because a fixture cannot state a
digest that moves and a case that cannot cite a real file cannot reach the checks that read
one. And `reached` counts those cases, because a seventh witness found the corpus checks
returning early on every case in the corpus while this printed "all proven".

`scripts/tests/test_fixture_coverage.py` is the other half: it disables one check at a time
and asserts this notices.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import copy
import json

from sovcoldstart import records
from sovcoldstart.report import GATES

def _apply(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Top-level replace. A patch that names a key owns that key's whole value.

    Shallow on purpose: `D-010` proves the refusal for a corpus block with no digest, and a
    deep merge would quietly restore the digest from the base and grade a case that never
    ran.
    """
    out = copy.deepcopy(base)
    out.update(copy.deepcopy(patch))
    return out


def cmd_selfcheck(args: Any) -> int:
    """Grade the run-record contract against its fixtures; fail if any refusal is unproven."""
    corpus = json.loads(records.CASES.read_text(encoding="utf-8"))
    schema = json.loads(records.SCHEMA.read_text(encoding="utf-8"))
    fired: set[str] = set()
    failures: list[str] = []
    reached = 0
    for case in corpus["cases"]:
        record = _bind_canonical(_apply(corpus["base_record"], case["patch"]))
        if (record.get("corpus") or {}).get("digest") == _canonical_digest():
            reached += 1
        found = records.defects(record, schema)
        codes = [d["code"] for d in found]
        fired.update(codes)
        # Exact, and a multiset. Subset grading let a refusal fire on a case that never
        # meant to test it; set grading then let one declared RECORD_SHAPE stand for eight
        # distinct shape defects. A case declares how many times each refusal fires.
        if sorted(case["expect"]) != sorted(codes):
            want = sorted(case["expect"]) or "an admissible record"
            detail = "; ".join("{code} ({detail})".format(**d) for d in found) or "none"
            failures.append(f"{case['case_id']}: expected {want}, got {detail}")
    unproven = [code for code in records.REFUSALS if code not in fired]
    if unproven:
        failures.append(f"declared refusals no case fires: {', '.join(unproven)}")
    if not reached:
        # A witness instrumented the corpus check and found it returned early on all 34
        # cases: the base record's digest is 64 zeros, so nothing ever bound the real
        # corpus, and `selfcheck` reported every refusal proven without reaching the code
        # that stops a record naming its own referent.
        failures.append("no case binds the canonical corpus, so every check that reads it "
                        "is unreachable from this oracle")

    structural = _corpus_defects(Path(args.corpus))
    for defect in structural:
        failures.append(f"corpus: {defect}")
    for line in failures:
        print(f"FAIL: {line}")
    if failures:
        return 1
    print(f"PASS: {len(corpus['cases'])} run-record case(s), "
          f"{len(records.REFUSALS)} refusal(s) all proven, corpus structurally sound")
    return 0


def _canonical_digest() -> str:
    """The digest of the corpus a run record is a reading of."""
    from sovcoldstart.refusals import CANONICAL_CORPUS

    return records.digest_of(records.ROOT / CANONICAL_CORPUS)


def _bind_canonical(record: dict[str, Any]) -> dict[str, Any]:
    """Substitute the live corpus into a case that asks for it by sentinel.

    A fixture cannot state a digest that changes every time the corpus does, so a case that
    needs to exercise the corpus-binding path says `CANONICAL` and gets the real values
    here. Its `run_id` is re-derived, because the digest is one of the four fields it comes
    from.
    """
    from sovcoldstart.refusals import CANONICAL_CORPUS

    out = record
    who = out.get("participant")
    if isinstance(who, dict) and who.get("answers_digest") == "DIGEST_OF_ANSWERS":
        cited = records.ROOT / str(who.get("answers", ""))
        if cited.is_file():
            out = {**out, "participant": {**who,
                                          "answers_digest": records.digest_of(cited)}}
    record = out
    corpus = record.get("corpus")
    if not isinstance(corpus, dict) or corpus.get("digest") != "CANONICAL":
        return record
    doc = json.loads((records.ROOT / CANONICAL_CORPUS).read_text(encoding="utf-8"))
    bound = {**corpus, "digest": _canonical_digest(), "questions": len(doc["questions"])}
    out = {**record, "corpus": bound}
    who = out.get("participant")
    out["run_id"] = "coldstart_" + records.run_identity(
        str((out.get("revision") or {}).get("commit")), bound["digest"],
        str(out.get("observed_at")), str(out.get("mode")),
        str(who.get("id", "")) if isinstance(who, dict) else "")
    return out


#: Keys that name where a probe reads, not what it looks for.
LOCATOR_KEYS = ("file", "path", "corpus", "dir")


def _strings(spec: Any, prefix: str = "") -> list[tuple[str, str]]:
    """Every string inside a probe spec, with the key path that reaches it."""
    out: list[tuple[str, str]] = []
    if isinstance(spec, dict):
        for key, value in spec.items():
            out.extend(_strings(value, f"{prefix}{key}"))
    elif isinstance(spec, list):
        for index, value in enumerate(spec):
            out.extend(_strings(value, f"{prefix}[{index}]"))
    elif isinstance(spec, str):
        out.append((prefix, spec))
    return out


def _corpus_defects(path: Path) -> list[str]:
    """What must be true of every question before any of them is worth asking.

    These are contract invariants, not probe results: a question with no tier is unscorable,
    and a probe whose search pattern contains the answer it is looking for measures nothing
    but itself. Both were real defects the first time this ran.
    """
    doc = json.loads(path.read_text(encoding="utf-8"))
    out, seen = [], set()
    for question in doc["questions"]:
        qid = question.get("id", "<unnamed>")
        if qid in seen:
            out.append(f"{qid}: duplicate id")
        seen.add(qid)
        for field in ("section", "tier", "q", "expected", "why", "severity_on_failure"):
            if field not in question:
                out.append(f"{qid}: no {field}")
        if question.get("tier") not in GATES:
            out.append(f"{qid}: tier {question.get('tier')!r} is not one of {sorted(GATES)}")
        # The question text is the only field a participant is handed, and nothing checked
        # whether the answer was sitting in it. "Is that grant RATIFIED?" expects RATIFIED.
        asked, want = question.get("q"), question.get("expected")
        if (isinstance(asked, str) and isinstance(want, str) and len(want) > 3
                and want.lower() in asked.lower()):
            out.append(f"{qid}: the question text contains its own expected answer")
        spec = question.get("probe")
        if not isinstance(spec, dict):
            continue
        # Two different defects, and the earlier version of this check confused them.
        #
        # A question carrying `probe_expected` asks the probe something different from what
        # it asks the participant: X23 asks whether AGENTS.md still contains one sentence,
        # while the participant has to say what the sentence means. A presence probe has to
        # name the thing whose presence it asserts, so containment there is the mechanism.
        # What is a defect is a pattern *equal to* what it is graded against: that reports a
        # sentence vanishing and can never report a rule changing.
        #
        # For every other question the value in the pattern is the answer being graded, and
        # a probe that searches for the answer it is checking measures only itself.
        if "probe_expected" in question:
            target, exact = question["probe_expected"], True
        else:
            target, exact = question.get("expected"), False
        # A list-valued `expected` is checked member by member. The guard used to skip
        # anything that was not a string, which was 90 of the 175 questions, and four probes
        # in that blind spot were alternations of their own answers - two of them tier 0.
        targets = target if isinstance(target, list) else [target]
        targets = [t for t in targets if isinstance(t, str) and len(t) > 3]
        if not targets:
            continue
        # Every string in the spec except the ones that say *where* to look. A witness
        # showed the same leak caught through `pattern` and invisible through `argv`, and
        # the spec uses nineteen keys across the corpus; but `file` and `path` are locators,
        # and a document named after the concept it settles - decisions/0023-acceptance-not-
        # approval.md, for a question whose answer is "acceptance" - is not a probe
        # searching for its own answer.
        for key, found in sorted(_strings(spec)):
            if key.split("[")[0] in LOCATOR_KEYS:
                continue
            hits = [t for t in targets if t.lower() in found.lower()]
            if len(targets) > 1 and len(hits) == len(targets):
                out.append(f"{qid}: probe {key} enumerates every one of its own expected "
                           f"values, so it can report one vanishing and never a new one "
                           f"appearing")
            elif len(targets) == 1 and hits:
                if found.strip().lower() == targets[0].strip().lower():
                    out.append(f"{qid}: probe {key} is its own expected value, so it can "
                               f"report the text vanishing and never the rule changing")
                elif not exact:
                    out.append(f"{qid}: probe {key} contains its own expected value")
    return out
