#!/usr/bin/env python3
"""Score how much the test suite actually asserts, by mutating what it tests.

Deliberately not part of `scripts/verify.py`: verify holds a three-second
budget and mutation scoring runs the suite once per mutant. This is a separate
command with its own budget, run as its own gate.

    python scripts/sov_mutate.py run --target scripts/sovschedule/cron.py
    python scripts/sov_mutate.py run --changed --threshold 80
    python scripts/sov_mutate.py selfcheck

`selfcheck` is the harness answering the question it exists to ask of everyone
else: it proves the scorer kills a mutant an asserting suite should catch and
spares one nothing asserts. A scorer that cannot demonstrate both is not
evidence about any other suite.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovmutate import harness, operators  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = ("tests", "lineage", ".git", "sovmutate")

SELFCHECK_SOURCE = """
def asserted(value):
    if value > 10:
        return "high"
    return "low"


def unasserted(value):
    if value > 10:
        return "high"
    return "low"
"""

SELFCHECK_SUITE = """
import unittest
import subject


class AssertedOnly(unittest.TestCase):
    def test_boundary_is_pinned(self):
        self.assertEqual(subject.asserted(11), "high")
        self.assertEqual(subject.asserted(10), "low")
"""


def _changed_files(base: str) -> list[Path]:
    """Python production files changed against ``base``."""
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD", "--", "*.py"],
        cwd=str(ROOT), capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return []
    files = []
    for name in result.stdout.split("\n"):
        name = name.strip()
        if not name:
            continue
        path = ROOT / name
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        files.append(path)
    return files


def command_run(args: argparse.Namespace) -> int:
    """Score one target, or every Python file the branch changed."""
    if args.changed:
        targets = _changed_files(args.base)
        if not targets:
            print(f"NOTHING TO SCORE: no production Python changed against {args.base}")
            return 0
    elif args.target:
        target = Path(args.target)
        targets = [target if target.is_absolute() else ROOT / target]
    else:
        print("REFUSED: name --target or pass --changed", file=sys.stderr)
        return 2

    total_killed = 0
    total_generated = 0
    for path in targets:
        if not path.is_file():
            print(f"REFUSED: {path} is not a file", file=sys.stderr)
            return 2
        score = harness.score_file(path, ROOT, limit=args.limit)
        print(harness.render(score))
        print()
        total_killed += score.killed
        total_generated += score.generated

    if total_generated == 0:
        print("NOTHING TO SCORE: the selected files admit no mutants")
        return 0

    percent = 100.0 * total_killed / total_generated
    print(f"R CHANNEL: {percent:.1f}% ({total_killed}/{total_generated} mutants killed)")
    if args.threshold is not None and percent < args.threshold:
        print(f"FAIL: mutation score {percent:.1f}% is below the {args.threshold:.1f}% threshold")
        return 1
    print("PASS: mutation scoring completed")
    return 0


def command_selfcheck(_args: argparse.Namespace) -> int:
    """Prove the scorer discriminates: it must kill one mutant and spare another."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        subject = workspace / "subject.py"
        subject.write_text(SELFCHECK_SOURCE, encoding="utf-8", newline="\n")
        (workspace / "test_subject.py").write_text(SELFCHECK_SUITE, encoding="utf-8", newline="\n")
        command = (sys.executable, "-m", "unittest", "discover", "-s", ".", "-q")
        score = harness.score_file(subject, workspace, command=command)

    asserted_lines = {3, 4, 5}
    killed_in_asserted = [m for m in score.mutants if m.killed and m.site.line in asserted_lines]
    survived_in_unasserted = [m for m in score.survived if m.site.line not in asserted_lines]

    print(harness.render(score))
    print()
    defects = []
    if not killed_in_asserted:
        defects.append("scorer killed no mutant in the asserted function; it cannot detect a real gap")
    if not survived_in_unasserted:
        defects.append("scorer spared no mutant in the unasserted function; it cannot be trusted to report a gap")
    if score.percent == 100.0:
        defects.append("scorer reported a perfect score against a suite that asserts only half the subject")

    for defect in defects:
        print(f"FAIL: {defect}", file=sys.stderr)
    if defects:
        return 1
    print("PASS: the scorer kills what is asserted and spares what is not")
    return 0


def command_sites(args: argparse.Namespace) -> int:
    """List the mutable sites in a file without running anything."""
    target = Path(args.target)
    path = target if target.is_absolute() else ROOT / target
    if not path.is_file():
        print(f"REFUSED: {path} is not a file", file=sys.stderr)
        return 2
    found = operators.sites(path.read_text(encoding="utf-8"))
    for site in found:
        print(f"  {path.name}:{site.line}  [{site.index}] {site.operator}  {site.description}")
    print(f"{len(found)} mutable site(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sov-mutate", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help=command_run.__doc__)
    run.add_argument("--target", help="file to score")
    run.add_argument("--changed", action="store_true", help="score every production Python file changed against --base")
    run.add_argument("--base", default="origin/main", help="comparison point for --changed")
    run.add_argument("--limit", type=int, default=None, help="cap mutants per file")
    run.add_argument("--threshold", type=float, default=None, help="fail below this kill percentage")
    run.set_defaults(handler=command_run)

    selfcheck = subparsers.add_parser("selfcheck", help=command_selfcheck.__doc__)
    selfcheck.set_defaults(handler=command_selfcheck)

    sites = subparsers.add_parser("sites", help=command_sites.__doc__)
    sites.add_argument("--target", required=True, help="file to inspect")
    sites.set_defaults(handler=command_sites)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except harness.RestoreFailure as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
