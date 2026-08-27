"""The verbs that make the benchmark a surface rather than a script.

`describe` answers what this benchmark is and what it offers, in JSON, so a fresh model can
find the operation without reading the source. `selfcheck` grades the run-record contract
against its own defeating fixtures and proves every declared refusal fires. `history` reads
the recorded runs back and names which sections moved between them, which is the whole
reason for a daily cadence.

`selfcheck` reaches `scripts/verify.py` through `scripts/tests/test_coldstart_records.py`
and `run_tooling_tests.py`, not as a named check: the check table in
`scripts/sovverify/checks.py` sits at the 300-line module ceiling. An earlier version of
this docstring said it was what verify runs, which was the shape the author intended rather
than the route it takes.

None of these settle standing. A run establishes `BUILT` and a benchmark cannot witness the
participant that ran it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from sovcoldstart import records
from sovcoldstart.oracle import cmd_selfcheck  # noqa: F401
from sovcoldstart.report import GATES, LABEL



def cmd_describe(args: Any) -> int:
    """Emit what this benchmark is and what it offers, for a reader that is not a human."""
    doc = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
    questions = doc["questions"]
    sections: dict[str, int] = {}
    tiers: dict[str, int] = {}
    for question in questions:
        sections[question["section"]] = sections.get(question["section"], 0) + 1
        tiers[str(question.get("tier"))] = tiers.get(str(question.get("tier")), 0) + 1
    manifest = {
        "surface": "cold-start-benchmark",
        "named_operation": "measure-cold-start-competence",
        "asks": "What does a participant know on arrival, before it reads a single file, and "
                "has the orientation layer told it the truth?",
        "corpus": {
            "path": Path(args.corpus).name,
            "digest": records.digest_of(Path(args.corpus)),
            "questions": len(questions),
            "sections": sections,
            "by_tier": tiers,
        },
        "tiers": [{"tier": tier, "label": LABEL[tier], "gate": GATES[tier],
                   "scored": GATES[tier] is not None} for tier in (0, 1, 2, 3)],
        "verbs": {
            "run": "grade the corpus against the world; DRIFT means `expected` is stale",
            "grade": "grade a participant's frozen answers against the probes",
            "rebase": "rewrite `expected` from current probe values, per section",
            "selfcheck": "prove the run-record contract still refuses what it declares",
            "describe": "this manifest",
            "history": "read recorded runs back and name the sections that moved",
        },
        "record": {
            "schema": records.SCHEMA.relative_to(records.ROOT).as_posix(),
            "written_to": records.RECORDS.relative_to(records.ROOT).as_posix(),
            "refusals": list(records.REFUSALS),
            "write_time_refusals": ["CORPUS_UNVERIFIED", "RECORD_WOULD_REPLACE"],
            "standing": "BUILT",
        },
        "settles": "nothing",
    }
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def cmd_paper(args: Any) -> int:
    """Emit the questions with every answer stripped, for handing to a participant.

    The corpus ships `expected` beside each question inside the repository the participant
    is being tested on, so anything that can read the tree can read the key. This does not
    fix that. What it fixes is the agent path: a launched participant is handed the paper in
    its prompt and never needs to open `corpus.json` at all, so passing by reading the key
    becomes a thing it has to decide to do rather than a thing it does by default.
    """
    doc = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
    paper = [
        {"id": q["id"], "section": q["section"], "tier": q["tier"], "q": q["q"],
         "answer_shape": q.get("answer_shape", _shape(q))}
        for q in doc["questions"]
        if not args.section or q["section"] in args.section
        if args.tier is None or q["tier"] in args.tier
    ]
    print(json.dumps({
        "paper_for": Path(args.corpus).name,
        "corpus_digest": records.digest_of(Path(args.corpus)),
        "questions": len(paper),
        "instruction": "Answer from what you already know. UNKNOWN is an admissible answer "
                       "and scores ABSTAIN, which is not the same as WRONG; a guess that "
                       "reads as confident is the failure this benchmark exists to catch.",
        "paper": paper,
    }, indent=2, ensure_ascii=False))
    return 0


def _shape(question: dict[str, Any]) -> str:
    """What form an answer has to take, without disclosing which answer it is."""
    grade = question.get("grade", "exact")
    if grade in ("int_eq", "int_tol"):
        return "one integer"
    if grade == "set_eq":
        return "a comma-separated set; order is not scored"
    if grade == "contains":
        return "one exact term or identifier"
    if grade == "manual":
        return "prose; graded by hand against a separate owner verdict"
    return "one exact value"


def cmd_history(args: Any) -> int:
    """Print the recorded runs and what changed between them."""
    runs = records.load_all()
    if not runs:
        print(f"no recorded runs under {records.RECORDS.relative_to(records.ROOT).as_posix()}")
        return 0
    if args.mode:
        runs = [r for r in runs if r["mode"] == args.mode]
    print(f"{'date':<11} {'mode':<11} {'participant':<26} {'verdict':<15} tier 0")
    for index, run in enumerate(runs):
        tiers = run.get("tiers") or []
        zero = next((t for t in tiers if isinstance(t, dict) and t.get("tier") == 0), {})
        holder = run.get("participant")
        who = holder.get("id", "-") if isinstance(holder, dict) else "-"
        flag = " !" + ",".join(run["_defects"]) if run["_defects"] else ""
        print(f"{str(run.get('observed_at', '?'))[:10]:<11} {str(run.get('mode', '?')):<11} "
              f"{who[:26]:<26} {str(run.get('verdict', '?')):<15} "
              f"{zero.get('hit', 0)}/{zero.get('scored', 0)}{flag}")
        if index:
            why = records.comparable(runs[index - 1], run)
            if why:
                print(f"            not comparable with the run above: {why}")
            else:
                for line in records.moved(runs[index - 1], run):
                    print(f"            moved  {line}")
    return 0
