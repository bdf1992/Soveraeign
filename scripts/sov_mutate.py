#!/usr/bin/env python3
"""Score how much the test suite actually asserts, by mutating what it tests.

Deliberately not part of `scripts/verify.py`: verify holds a fifteen-second
budget and mutation scoring runs the suite once per mutant. This is a separate
command with its own budget, run as its own gate.

    python scripts/sov_mutate.py run --target scripts/sovschedule/cron.py
    python scripts/sov_mutate.py run --changed --threshold 80
    python scripts/sov_mutate.py selfcheck

`selfcheck` is the harness answering the question it exists to ask of everyone
else: it proves the scorer kills a mutant an asserting suite should catch,
spares one nothing asserts, and that diff-scoped scoring reaches only mutable
sites on lines the change actually touched. A scorer that cannot demonstrate
those properties is not evidence about any other suite.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovmutate import harness, operators  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = ("tests", "lineage", ".git", "sovmutate")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


class DiffScopeError(RuntimeError):
    """The changed-file or changed-line scope could not be derived honestly."""


# Which suite actually exercises a file. Running the wrong suite scores zero and
# reads as "nothing asserts this", which is a false alarm rather than a finding -
# the first CI run reported conformance/run.py at 0.0% for exactly that reason,
# because it was being scored against scripts/tests. A file whose owning suite is
# not listed here is refused, never scored: a number nobody can trust is worse
# than an honest gap.
SUITES = (
    ("conformance", ("-m", "unittest", "discover", "-s", "conformance/tests", "-q"), ROOT),
    (str(Path("bindings/sov")), ("-m", "unittest", "discover", "-s", "bindings/sov/tests", "-q"), ROOT),
    (str(Path("services/asset")), ("-m", "unittest", "discover", "-s", "tests", "-q"), ROOT / "services" / "asset"),
    (str(Path("services/console")), ("-m", "unittest", "discover", "-s", "tests", "-q"), ROOT / "services" / "console"),
    (str(Path("services/host")), ("-m", "unittest", "discover", "-s", "tests", "-q"), ROOT / "services" / "host"),
    (str(Path("adapters/host")), ("-m", "unittest", "discover", "-s", "tests", "-q"), ROOT / "services" / "host"),
    (str(Path("services/registry")), ("-m", "unittest", "scripts.tests.test_registry_horizontal", "-q"), ROOT),
    (str(Path("scripts/sov_mutate.py")), ("scripts/sov_mutate.py", "selfcheck"), ROOT),
    (str(Path("scripts/sovmutate")), ("scripts/sov_mutate.py", "selfcheck"), ROOT),
    (str(Path("scripts/sov_capability.py")), ("-m", "unittest", "scripts.tests.test_capability_map", "-q"), ROOT),
    (str(Path("scripts/sovkernel/capability_map.py")), ("-m", "unittest", "scripts.tests.test_capability_map", "-q"), ROOT),
    (str(Path("scripts/sovschedule")), (
        "-m", "unittest",
        "scripts.tests.test_automation_authoring",
        "scripts.tests.test_automation_control",
        "scripts.tests.test_automation_health",
        "scripts.tests.test_automation_intent",
        "-q",
    ), ROOT),
    ("scripts", ("-m", "unittest", "discover", "-s", "scripts/tests", "-q"), ROOT),
)


def suite_for(path: Path) -> tuple[tuple[str, ...], Path] | None:
    """The (command, cwd) that exercises ``path``, or None if nothing claims it."""
    try:
        relative = str(path.resolve().relative_to(ROOT))
    except ValueError:
        return None
    for prefix, argv, cwd in SUITES:
        if relative == prefix or relative.startswith(prefix + "\\") or relative.startswith(prefix + "/"):
            return (sys.executable,) + argv, cwd
    return None


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
        raise DiffScopeError(
            f"git diff could not derive changed Python files against {base}: "
            f"{result.stderr.strip() or f'exit {result.returncode}'}")
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


def _parse_changed_lines(diff: str) -> set[int]:
    """New-side line numbers named by zero-context unified-diff hunks."""
    changed: set[int] = set()
    for row in diff.splitlines():
        match = HUNK.match(row)
        if match is None:
            continue
        start = int(match.group(1))
        count = int(match.group(2) or "1")
        changed.update(range(start, start + count))
    return changed


def _changed_lines(base: str, path: Path, root: Path = ROOT) -> set[int]:
    """The new-side lines in ``path`` changed against ``base``."""
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise DiffScopeError(f"{path} is outside mutation root {root}") from exc
    shown = str(relative).replace("\\", "/")
    result = subprocess.run(
        ["git", "diff", "--unified=0", "--no-color", f"{base}...HEAD", "--", shown],
        cwd=str(root), capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise DiffScopeError(
            f"git diff could not derive changed lines for {shown} against {base}: "
            f"{result.stderr.strip() or f'exit {result.returncode}'}")
    return _parse_changed_lines(result.stdout)


def _budgeted_targets(
    targets: list[Path], per_file_limit: int | None, total_limit: int | None,
) -> tuple[list[tuple[Path, int | None]], list[Path]]:
    """Bound a run while sampling across the complete ordered target set.

    A per-file cap alone multiplies with the size of a reconciliation diff.  If
    the whole-run cap cannot reach every file, evenly spaced paths are selected
    so the result does not silently become a prefix-of-the-tree score.
    """
    if per_file_limit is not None and per_file_limit < 1:
        raise ValueError("--limit must be at least 1")
    if total_limit is None:
        return [(path, per_file_limit) for path in targets], []
    if total_limit < 1:
        raise ValueError("--total-limit must be at least 1")
    if not targets:
        return [], []

    selected_count = min(len(targets), total_limit)
    if selected_count == len(targets):
        indices = list(range(len(targets)))
    elif selected_count == 1:
        indices = [len(targets) // 2]
    else:
        indices = [round(index * (len(targets) - 1) / (selected_count - 1))
                   for index in range(selected_count)]
    selected = set(indices)
    share = max(1, total_limit // selected_count)
    file_limit = min(per_file_limit, share) if per_file_limit is not None else share
    planned = [(path, file_limit) for index, path in enumerate(targets) if index in selected]
    omitted = [path for index, path in enumerate(targets) if index not in selected]
    return planned, omitted


def command_run(args: argparse.Namespace) -> int:
    """Score one target, or mutable sites on changed lines in changed Python files."""
    line_scope: dict[Path, set[int]] = {}
    if args.changed:
        targets = _changed_files(args.base)
        if not targets:
            print(f"NOTHING TO SCORE: no production Python changed against {args.base}")
            return 0
        line_scope = {path: _changed_lines(args.base, path) for path in targets}
    elif args.target:
        target = Path(args.target)
        targets = [target if target.is_absolute() else ROOT / target]
    else:
        print("REFUSED: name --target or pass --changed", file=sys.stderr)
        return 2

    unclaimed = [path for path in targets if suite_for(path) is None]
    claimed = [path for path in targets if suite_for(path) is not None]
    try:
        planned, budget_omitted = _budgeted_targets(
            claimed, args.limit, args.total_limit)
    except ValueError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    if args.total_limit is not None:
        per_file = planned[0][1] if planned else 0
        print(f"WHOLE-RUN CAP: at most {args.total_limit} mutants; "
              f"{len(planned)}/{len(claimed)} claimed files sampled; "
              f"at most {per_file} mutant(s) per sampled file")
        print()

    total_killed = 0
    total_generated = 0
    for path, file_limit in planned:
        if not path.is_file():
            print(f"REFUSED: {path} is not a file", file=sys.stderr)
            return 2
        suite = suite_for(path)
        assert suite is not None
        command, cwd = suite
        scoped_lines = line_scope.get(path)
        if scoped_lines is not None:
            print(f"DIFF SCOPE: {path.relative_to(ROOT)} has {len(scoped_lines)} changed new-side line(s)")
        score = harness.score_file(
            path, cwd, command=command, limit=file_limit, lines=scoped_lines)
        print(harness.render(score))
        print()
        total_killed += score.killed
        total_generated += score.generated

    for path in unclaimed:
        print(f"UNSCORED: no suite in SUITES claims {path}; not counted in the channel")
    for path in budget_omitted:
        print(f"UNSCORED: whole-run cap sampled out {path}; not counted in the channel")

    if total_generated == 0:
        print("NOTHING TO SCORE: changed lines admit no mutants from the current operator set")
        return 0

    percent = 100.0 * total_killed / total_generated
    print(f"R CHANNEL: {percent:.1f}% ({total_killed}/{total_generated} mutants killed)")
    if args.threshold is not None and percent < args.threshold:
        print(f"FAIL: mutation score {percent:.1f}% is below the {args.threshold:.1f}% threshold")
        return 1
    print("PASS: mutation scoring completed")
    return 0


def command_selfcheck(_args: argparse.Namespace) -> int:
    """Prove the scorer discriminates and honors changed-line scope."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        subject = workspace / "subject.py"
        subject.write_text(SELFCHECK_SOURCE, encoding="utf-8", newline="\n")
        (workspace / "test_subject.py").write_text(SELFCHECK_SUITE, encoding="utf-8", newline="\n")
        command = (sys.executable, "-m", "unittest", "discover", "-s", ".", "-q")
        score = harness.score_file(subject, workspace, command=command)
        asserted_lines = {3, 4, 5}
        focused = harness.score_file(subject, workspace, command=command, lines=asserted_lines)

    killed_in_asserted = [m for m in score.mutants if m.killed and m.site.line in asserted_lines]
    survived_in_unasserted = [m for m in score.survived if m.site.line not in asserted_lines]

    print(harness.render(score))
    print()
    print("focused diff-scope control:")
    print(harness.render(focused))
    print()
    defects = []
    if not killed_in_asserted:
        defects.append("scorer killed no mutant in the asserted function; it cannot detect a real gap")
    if not survived_in_unasserted:
        defects.append("scorer spared no mutant in the unasserted function; it cannot be trusted to report a gap")
    if score.percent == 100.0:
        defects.append("scorer reported a perfect score against a suite that asserts only half the subject")
    if not focused.mutants:
        defects.append("diff-scoped scorer selected no mutant from the asserted lines")
    if focused.survived:
        defects.append("diff-scoped scorer spared a mutant on the fully asserted changed-line control")
    if any(mutant.site.line not in asserted_lines for mutant in focused.mutants):
        defects.append("diff-scoped scorer mutated a site outside the supplied changed-line set")
    if focused.scoped_out == 0:
        defects.append("diff-scoped scorer did not report excluding the unasserted function")

    parsed = _parse_changed_lines(
        "@@ -3,2 +3,3 @@\n-old\n+new\n@@ -10 +11,0 @@\n-gone\n@@ -15 +15,2 @@\n+a\n+b\n")
    if parsed != {3, 4, 5, 15, 16}:
        defects.append(f"zero-context diff parser returned {sorted(parsed)}, not [3, 4, 5, 15, 16]")

    for defect in defects:
        print(f"FAIL: {defect}", file=sys.stderr)
    if defects:
        return 1
    print("PASS: the scorer discriminates and diff scope reaches only changed lines")
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
    parser = argparse.ArgumentParser(prog="sov-mutate", description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help=command_run.__doc__)
    run.add_argument("--target", help="file to score")
    run.add_argument(
        "--changed", action="store_true",
        help="score mutable sites on changed lines of production Python files against --base")
    run.add_argument("--base", default="origin/main", help="comparison point for --changed")
    run.add_argument("--limit", type=int, default=None, help="cap mutants per file")
    run.add_argument("--total-limit", type=int, default=None,
                     help="cap mutants across the run and sample files evenly")
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
    except (harness.RestoreFailure, DiffScopeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
