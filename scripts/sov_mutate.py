#!/usr/bin/env python3
"""Score how much the test suite asserts by mutating what the change touches.

`run --changed` mutates mutable sites on new-side lines in the merge-base diff,
not every historical branch in every touched file. The whole-run mutant cap and
per-file cap still bound cost. `selfcheck` proves the scorer discriminates and
that diff scoping cannot silently widen beyond the supplied changed lines.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovmutate import diffscope, harness, operators, suites  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

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


def _budgeted_targets(
    targets: list[Path], per_file_limit: int | None, total_limit: int | None,
) -> tuple[list[tuple[Path, int | None]], list[Path]]:
    """Bound a run while sampling across the complete ordered target set."""
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
        indices = [round(i * (len(targets) - 1) / (selected_count - 1))
                   for i in range(selected_count)]
    selected = set(indices)
    share = max(1, total_limit // selected_count)
    file_limit = min(per_file_limit, share) if per_file_limit is not None else share
    planned = [(path, file_limit) for i, path in enumerate(targets) if i in selected]
    omitted = [path for i, path in enumerate(targets) if i not in selected]
    return planned, omitted


def command_run(args: argparse.Namespace) -> int:
    """Score one target, or changed-line mutation sites in changed Python files."""
    line_scope: dict[Path, set[int]] = {}
    if args.changed:
        targets = diffscope.changed_files(ROOT, args.base)
        if not targets:
            print(f"NOTHING TO SCORE: no production Python changed against {args.base}")
            return 0
        line_scope = {path: diffscope.changed_lines(ROOT, args.base, path) for path in targets}
    elif args.target:
        target = Path(args.target)
        targets = [target if target.is_absolute() else ROOT / target]
    else:
        print("REFUSED: name --target or pass --changed", file=sys.stderr)
        return 2

    unclaimed = [path for path in targets if suites.suite_for(path, ROOT) is None]
    claimed = [path for path in targets if suites.suite_for(path, ROOT) is not None]
    try:
        planned, budget_omitted = _budgeted_targets(claimed, args.limit, args.total_limit)
    except ValueError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    if args.total_limit is not None:
        per_file = planned[0][1] if planned else 0
        print(f"WHOLE-RUN CAP: at most {args.total_limit} mutants; "
              f"{len(planned)}/{len(claimed)} claimed files sampled; "
              f"at most {per_file} mutant(s) per sampled file\n")

    total_killed = 0
    total_generated = 0
    for path, file_limit in planned:
        if not path.is_file():
            print(f"REFUSED: {path} is not a file", file=sys.stderr)
            return 2
        owned = suites.suite_for(path, ROOT)
        assert owned is not None
        command, cwd = owned
        scoped_lines = line_scope.get(path)
        if scoped_lines is not None:
            print(f"DIFF SCOPE: {path.relative_to(ROOT)} has {len(scoped_lines)} changed line(s)")
        score = harness.score_file(
            path, cwd, command=command, limit=file_limit, lines=scoped_lines)
        print(harness.render(score), "\n")
        total_killed += score.killed
        total_generated += score.generated

    for path in unclaimed:
        print(f"UNSCORED: no suite claims {path}; not counted in the channel")
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
    """Prove discrimination, diff scope, parser behavior, and specific suite ownership."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        subject = workspace / "subject.py"
        subject.write_text(SELFCHECK_SOURCE, encoding="utf-8", newline="\n")
        (workspace / "test_subject.py").write_text(SELFCHECK_SUITE, encoding="utf-8", newline="\n")
        command = (sys.executable, "-m", "unittest", "discover", "-s", ".", "-q")
        score = harness.score_file(subject, workspace, command=command)
        asserted_lines = {3, 4, 5}
        focused = harness.score_file(subject, workspace, command=command, lines=asserted_lines)

    print(harness.render(score), "\n\nfocused diff-scope control:")
    print(harness.render(focused), "\n")
    defects: list[str] = []
    if not any(m.killed and m.site.line in asserted_lines for m in score.mutants):
        defects.append("scorer killed no mutant in the asserted function")
    if not any(m.site.line not in asserted_lines for m in score.survived):
        defects.append("scorer spared no mutant in the unasserted function")
    if score.percent == 100.0:
        defects.append("scorer reported a perfect score against a half-asserted subject")
    if not focused.mutants or focused.survived:
        defects.append("diff-scoped asserted control was not fully killed")
    if any(m.site.line not in asserted_lines for m in focused.mutants):
        defects.append("diff scope mutated a site outside the supplied changed lines")
    if focused.scoped_out == 0:
        defects.append("diff scope did not report excluding the unasserted function")

    parsed = diffscope.parse_changed_lines(
        "@@ -3,2 +3,3 @@\n-old\n+new\n@@ -10 +11,0 @@\n-gone\n@@ -15 +15,2 @@\n+a\n+b\n")
    if parsed != {3, 4, 5, 15, 16}:
        defects.append(f"diff parser returned {sorted(parsed)}, not [3, 4, 5, 15, 16]")

    capability = suites.suite_for(ROOT / "scripts/sov_capability.py", ROOT)
    scheduler = suites.suite_for(ROOT / "scripts/sovschedule/authoring.py", ROOT)
    if capability is None or "scripts.tests.test_capability_map" not in capability[0]:
        defects.append("capability mutation target is not owned by its focused suite")
    if scheduler is None or "scripts.tests.test_automation_authoring" not in scheduler[0]:
        defects.append("scheduler mutation target is not owned by its focused suite")

    for defect in defects:
        print(f"FAIL: {defect}", file=sys.stderr)
    if defects:
        return 1
    print("PASS: the scorer discriminates, scopes the diff, and resolves focused suite owners")
    return 0


def command_sites(args: argparse.Namespace) -> int:
    """List mutable sites in a file without running anything."""
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
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help=command_run.__doc__)
    run.add_argument("--target", help="file to score")
    run.add_argument("--changed", action="store_true", help="score changed-line mutation sites")
    run.add_argument("--base", default="origin/main", help="comparison point for --changed")
    run.add_argument("--limit", type=int, default=None, help="cap mutants per file")
    run.add_argument("--total-limit", type=int, default=None, help="cap mutants across the run")
    run.add_argument("--threshold", type=float, default=None, help="fail below this kill percentage")
    run.set_defaults(handler=command_run)
    selfcheck = sub.add_parser("selfcheck", help=command_selfcheck.__doc__)
    selfcheck.set_defaults(handler=command_selfcheck)
    sites = sub.add_parser("sites", help=command_sites.__doc__)
    sites.add_argument("--target", required=True, help="file to inspect")
    sites.set_defaults(handler=command_sites)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except (harness.RestoreFailure, diffscope.DiffScopeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
