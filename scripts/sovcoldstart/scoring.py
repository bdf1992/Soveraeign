"""The three verbs that score something: the corpus, a participant, or the key itself.

Split out of `sov_coldstart.py` so the entry point owns argument parsing and dispatch and
nothing else. These three share the probe loop, the owner-verdict rules and the record
writer; the CLI shares none of it.

`run` grades the corpus against the world, `grade` grades a participant against the probes,
and `rebase` rewrites `expected` where the world has moved. They are separate verbs because
they are separate readings, and averaging them would hide which one moved.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import re

from sovcoldstart import records
from sovcoldstart.submission import _graded_by, _inside, keep, load_verdicts
from sovcoldstart.grading import UNMEASURED, compare, judge, truth_for
from sovcoldstart.probes import FAST_COSTS, ProbeError, cost_of, execute, pin
from sovcoldstart.report import scorecard

GRADES = ("exact", "int_eq", "int_tol", "set_eq", "contains", "manual")
STATUSES = ("MATCH", "DRIFT", "ERROR", "MANUAL", "SKIPPED")


def probe_one(question: dict[str, Any], offline: bool, fast: bool = False) -> tuple[str, Any, str]:
    """Return (status, actual, detail) for one question.

    A procedural or defeating-case question may carry `probe_expected`: the probe then
    asserts that the procedure or contract it names is still live, while `expected` stays
    the answer a participant has to give. The two are graded separately on purpose.
    """
    spec = question.get("probe")
    if spec is None:
        return ("MANUAL", None, "no automatic probe; the owner grades this one")
    cost = cost_of(spec)
    if offline and (question.get("network") or cost == "NET"):
        return ("SKIPPED", None, "network probe skipped under --offline")
    if fast and cost not in FAST_COSTS:
        return ("SKIPPED", None, f"{cost} probe skipped under --fast")
    try:
        actual = execute(spec)
    except (ProbeError, OSError, ValueError, KeyError, IndexError, TypeError,
            re.error) as exc:
        return ("ERROR", None, f"{type(exc).__name__}: {exc}")
    if "probe_expected" in question:
        target = question["probe_expected"]
        grade, tol = ("int_eq" if isinstance(target, int) else "contains"), 0
    elif question.get("grade") == "manual":
        return ("MANUAL", actual, "probe recorded the environment; the answer is graded by hand")
    else:
        target, grade, tol = question["expected"], question.get("grade", "exact"), question.get("tol", 0)
    try:
        ok = compare(target, actual, grade, tol)
    except (TypeError, ValueError) as exc:
        return ("ERROR", actual, f"grader {grade!r} cannot compare these: {exc}")
    return ("MATCH" if ok else "DRIFT", actual, "")


def load_corpus(path: Path) -> dict[str, Any]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    for question in doc["questions"]:
        if question["id"] in seen:
            raise SystemExit(f"duplicate question id {question['id']}")
        if question.get("grade", "exact") not in GRADES:
            raise SystemExit(f"{question['id']}: unknown grader {question.get('grade')!r}")
        seen.add(question["id"])
    return doc



def _short(value: Any, width: int = 58) -> str:
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 1] + "…"


def cmd_run(args: argparse.Namespace) -> int:
    doc = load_corpus(args.corpus)
    print(f"pinned at {pin()[:12]}")
    questions = [q for q in doc["questions"] if not args.section or q["section"] in args.section]
    results: list[dict[str, Any]] = []
    for question in questions:
        status, actual, detail = probe_one(question, args.offline, args.fast)
        results.append({**question, "status": status, "actual": actual, "detail": detail})
        if status == "DRIFT":
            print(f"DRIFT  {question['id']} {question['section']:<12} {_short(question['q'])}")
            print(f"       expected {_short(question['expected'])}")
            print(f"       probe    {_short(actual)}")
        elif status == "ERROR":
            print(f"ERROR  {question['id']} {question['section']:<12} {detail}")
        elif args.verbose:
            print(f"{status:<6} {question['id']} {question['section']:<12} {_short(actual)}")

    tally = {name: sum(1 for r in results if r["status"] == name) for name in STATUSES}
    print()
    card, _ = scorecard(results, "status", "MATCH", "SOVERAEIGN COLD-START CORPUS INTEGRITY")
    print(card)
    print(" ".join(f"{name}={tally[name]}" for name in STATUSES) + f" total={len(results)}")
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
        print(f"\nwrote {args.json}")
    keep(args, results, "status", "MATCH", doc, "INTEGRITY")
    if tally["ERROR"]:
        print("\nERROR means the benchmark is broken, not the repository. Repair the probe.")
        return 1
    if tally["DRIFT"]:
        print(
            "\nDRIFT means `expected` and the world disagree. Decide which is wrong before"
            "\nrebasing; never widen a tolerance to make a mismatch disappear."
        )
        return 1 if args.strict else 0
    return 0


def cmd_grade(args: argparse.Namespace) -> int:
    doc = load_corpus(args.corpus)
    pin()
    submission = json.loads(args.answers.read_text(encoding="utf-8"))
    answers = {a["id"]: a for a in submission["answers"]}
    verdicts = load_verdicts(args)
    scored: list[dict[str, Any]] = []
    for question in doc["questions"]:
        if args.section and question["section"] not in args.section:
            continue
        status, actual, _ = probe_one(question, args.offline, args.fast)
        answer = answers.get(question["id"], {})
        given = answer.get("value")
        truth = truth_for(question, status, actual)
        verdict = judge(question, given, truth, verdicts.get(question["id"]))
        scored.append({**question, "given": given, "truth": truth, "verdict": verdict})
        if verdict in ("WRONG", "MISSING", "UNGRADED") or args.verbose:
            print(f"{verdict:<8} {question['id']} {question['section']:<12} {_short(question['q'])}")
            if verdict not in ("MISSING", "UNGRADED"):
                print(f"         answered {_short(given)}")
                if args.reveal:
                    print(f"         actual   {_short(truth)}")

    right = sum(1 for s in scored if s["verdict"] == "RIGHT")
    wrong = sum(1 for s in scored if s["verdict"] == "WRONG")
    abstain = sum(1 for s in scored if s["verdict"] == "ABSTAIN")
    missing = sum(1 for s in scored if s["verdict"] == "MISSING")
    print()
    card, admissible = scorecard(scored, "verdict", "RIGHT", "SOVERAEIGN COLD-START COMPETENCE REPORT")
    print(card)
    attempted = right + wrong
    print(f"RIGHT={right} WRONG={wrong} ABSTAIN={abstain} MISSING={missing} total={len(scored)}")
    print(f"coverage: {attempted}/{len(scored)} = {100 * attempted / max(1, len(scored)):.0f}% "
          f"(ABSTAIN and MISSING are unattempted, not wrong)")
    if args.json:
        Path(args.json).write_text(json.dumps(scored, indent=1) + "\n", encoding="utf-8",
                                   newline="\n")
        print(f"\nwrote {args.json}")
    manual = [s for s in scored if s.get("grade") == "manual"]
    keep(
        args, scored, "verdict", "RIGHT", doc, "COMPETENCE",
        participant={
            "id": submission.get("participant", args.participant or "unattributed"),
            "host": submission.get("binding", "unstated"),
            "answers": _inside(args.answers) or args.answers.as_posix(),
            "answers_digest": records.digest_of(args.answers),
        },
        graded_by=_graded_by(args, manual) if args.record else None,
    )
    return 0 if admissible else 1


def cmd_rebase(args: argparse.Namespace) -> int:
    """Rewrite expectations the world has moved past. This verb writes the answer key.

    Two guards, both found missing by a witness. Tier 0 questions assert doctrine, and a
    wrong tier 0 expectation teaches every future participant the wrong rule with the weight
    of a failed gate behind it; `decisions/0078` says never rebase one without a decision
    record, and this is that sentence in code rather than in prose.

    The second guard is narrower and was worse. A question carrying `probe_expected` has its
    probe compared against that field, not against `expected` - the two ask different
    questions on purpose. Rebasing wrote the probe value into `expected` anyway, so a DRIFT
    about whether a protected boundary is still declared rewrote the answer to "what happens
    when a builder witnesses its own change" as the integer 1.
    """
    doc = load_corpus(args.corpus)
    changed = held = 0
    for question in doc["questions"]:
        if args.section and question["section"] not in args.section:
            continue
        if args.volatility and question.get("volatility") not in args.volatility:
            continue
        status, actual, _ = probe_one(question, args.offline, args.fast)
        if status != "DRIFT":
            continue
        field = "probe_expected" if "probe_expected" in question else "expected"
        if question.get("tier") == 0 and not args.tier_zero_ruling:
            print(f"HELD  {question['id']} tier 0: {_short(question[field])} -> "
                  f"{_short(actual)}")
            print(f"      {question.get('why', '')[:70]}")
            held += 1
            continue
        print(f"{question['id']}: {field} {_short(question[field])} -> {_short(actual)}")
        question[field] = actual
        changed += 1
    if held:
        print(f"\n{held} tier 0 expectation(s) held. A tier 0 question states a rule, so its "
              f"\nexpectation moving means the rule changed. Record that in decisions/ and "
              f"\npass --tier-zero-ruling <path> to rebase it.")
    if not changed:
        print("nothing drifted; corpus already describes the world")
        return 0
    if args.dry_run:
        print(f"\n{changed} entr(ies) would change. Re-run without --dry-run to write.")
        return 0
    args.corpus.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"\nrewrote {changed} expectation(s) in {args.corpus}")
    return 0
