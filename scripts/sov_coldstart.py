#!/usr/bin/env python3
"""Grade what a participant knows on arrival against what the system actually holds.

A fresh session is oriented by CLAUDE.md, AGENTS.md and its memory before it reads a
single file. Those pages go stale silently, and every launched agent reads them as
current. This command turns that orientation into a scored corpus: each question carries
a deterministic probe that recomputes the answer from the live repository, host, or
GitHub, so the benchmark never needs a hand-maintained answer key.

    run        execute every probe and report where `expected` has drifted from the world
    grade      score a participant's frozen answers against the probes
    rebase     rewrite `expected` from the current probe values, for sections that moved
    selfcheck  prove the run-record contract still refuses what it declares
    describe   emit the surface manifest, for a reader that is not a human
    paper      emit the questions with every answer stripped, to hand to a participant
    history    read the recorded runs back and name the sections that moved

`run` reports drift and exits 0. `--strict` makes drift a failure. A probe that cannot
produce a value is ERROR, never PASS: an unanswerable question is not a correct one.

Nothing here settles standing. `AGENTS.md`: a test may establish `BUILT`; it may never
claim `WITNESSED` or `RATIFIED`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import sys

from sovcoldstart.scoring import cmd_grade, cmd_rebase, cmd_run
from sovcoldstart.verbs import cmd_describe, cmd_history, cmd_paper, cmd_selfcheck

CORPUS = Path(__file__).resolve().parent / "sovcoldstart" / "corpus.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpus", type=Path, default=CORPUS)
    parser.add_argument("--section", action="append", help="limit to a section; repeatable")
    parser.add_argument("--offline", action="store_true", help="skip probes that need network")
    parser.add_argument("--fast", action="store_true",
                        help="file and git probes only; skips every repository gate subprocess")
    parser.add_argument("--json", help="write the full result set to this path")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--reveal", action="store_true",
                        help="print the truth beside a wrong answer; off by default because "
                             "the previous behaviour let a participant read the key off stdout "
                             "and resubmit")
    parser.add_argument("--record", action="store_true",
                        help="write a run record under reports/coldstart/ so tomorrow's card "
                             "can be compared with today's")
    parser.add_argument("--at", default=None,
                        help="observation timestamp for the record; defaults to now, and is "
                             "settable so a run can be replayed and produce the same record")
    parser.add_argument("--participant", default=None,
                        help="who is being graded, when the answers file does not say")
    subs = parser.add_subparsers(dest="verb", required=True)
    subs.add_parser("run").add_argument("--strict", action="store_true", help="drift fails")
    grade = subs.add_parser("grade")
    grade.add_argument("answers", type=Path, help="JSON file with an `answers` list")
    grade.add_argument("--owner-verdicts", type=Path,
                       help="separate file of owner verdicts on the manual questions; without "
                            "it every manual question reads UNGRADED, which is the honest state")
    rebase = subs.add_parser("rebase")
    rebase.add_argument("--volatility", action="append", help="limit to a volatility class")
    rebase.add_argument("--dry-run", action="store_true")
    rebase.add_argument("--tier-zero-ruling", type=Path,
                        help="path to the decision record that settles a tier 0 expectation "
                             "moving; without it tier 0 questions are held, because a tier 0 "
                             "expectation that moved is a rule that changed")
    subs.add_parser("selfcheck", help="prove the run-record contract still refuses what it "
                                      "declares, and the corpus is structurally sound")
    subs.add_parser("describe", help="emit the surface manifest as JSON")
    subs.add_parser("paper", help="emit the questions with every answer stripped"
                    ).add_argument("--tier", action="append", type=int,
                                   help="limit to a tier; repeatable")
    subs.add_parser("history", help="read recorded runs back and name the sections that moved"
                    ).add_argument("--mode", choices=("INTEGRITY", "COMPETENCE"))
    return parser


def _check_ruling(path: Path) -> None:
    """A tier 0 rebase is authorised by a decision record, not by any file that exists.

    The first version of this guard accepted anything `is_file()` admitted: a witness
    unlocked a tier 0 rewrite with an empty .txt in a temp directory. A tier 0 expectation
    states a rule, so what authorises changing it has to be the thing this repository uses
    to change rules.
    """
    root = Path(__file__).resolve().parent.parent
    try:
        inside = path.resolve().relative_to(root)
    except ValueError:
        raise SystemExit(f"{path} is outside the repository; a tier 0 rebase is authorised "
                         f"by a decision record under decisions/") from None
    if inside.parts[0] != "decisions" or inside.suffix != ".md":
        raise SystemExit(f"{inside.as_posix()} is not a decision record; a tier 0 expectation "
                         f"states a rule and changing it is a ruling, not an edit")
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        raise SystemExit(f"{inside.as_posix()} is empty or missing")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.strict = getattr(args, "strict", False)
    args.owner_verdicts = getattr(args, "owner_verdicts", None)
    args.mode = getattr(args, "mode", None)
    args.tier = getattr(args, "tier", None)
    args.tier_zero_ruling = getattr(args, "tier_zero_ruling", None)
    if args.tier_zero_ruling:
        _check_ruling(args.tier_zero_ruling)
    args.at = args.at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    verbs = {"run": cmd_run, "grade": cmd_grade, "rebase": cmd_rebase,
             "selfcheck": cmd_selfcheck, "describe": cmd_describe, "paper": cmd_paper,
             "history": cmd_history}
    return verbs[args.verb](args)


if __name__ == "__main__":
    sys.exit(main())
