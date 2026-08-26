"""What the repository says: branches, ranges, paths, and the checks a grant names.

Split out of `scripts/sov_land.py` on 2026-08-25, when the gate crossed the
300-line module budget for the second time in a day. This half reads the tree
and answers factual questions about it. The half next door decides what those
answers mean against a grant and performs whatever the verdict permits.

Everything here touches the filesystem or git, which is exactly what
`sovkernel/authority.py` refuses to do. That division is deliberate: the
evaluator stays pure so its corpus can grade it in an empty directory, and the
questions that genuinely need a repository are asked here instead.
"""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


class LandingRefused(Exception):
    """The gate cannot honestly grade this landing, so it refuses instead of failing."""


def _git(*argv: str) -> str:
    """Run one git command in the repository root and return its stdout."""
    done = subprocess.run(["git", *argv], cwd=ROOT, capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError(f"git {' '.join(argv)} failed: {done.stderr.strip()}")
    return done.stdout


def current_branch() -> str:
    return _git("rev-parse", "--abbrev-ref", "HEAD").strip()


def dirty_paths() -> list[str]:
    """Every path git reports as changed, in porcelain order."""
    lines = [line for line in _git("status", "--porcelain").splitlines() if line.strip()]
    return [line[3:].strip().strip('"').split(" -> ")[-1] for line in lines]


def _run_check(name: str, argv: list[str]) -> str:
    """Run one repository check and reduce it to PASS or FAIL."""
    done = subprocess.run([sys.executable, *argv], cwd=ROOT, capture_output=True, text=True)
    return "PASS" if done.returncode == 0 else "FAIL"


def gather_checks(skip: bool) -> dict[str, str]:
    """Run the checks the grant names as preconditions."""
    if skip:
        return {}
    return {
        "lint": _run_check("lint", ["scripts/lint.py"]),
        "verify": _run_check("verify", ["scripts/verify.py"]),
    }


def carried_paths(target: str, branch: str) -> list[str]:
    """Every path the merge would move onto the target.

    `--path` says what this landing stages. It never said what the merge carries.
    `git merge --no-ff` moves every commit already on the branch, and those paths
    were never shown to the evaluator, so the exclusion list was not decorative -
    it was simply not asked. Reproduced on 2026-08-25 in a throwaway clone:
    `.github/probe-workflow.yml`, which the standing grant excludes by name,
    reached the target PERMITTED while the gate was only ever asked about
    `scripts/lint.py`.

    `decisions/0064` names a landed commit touching `decisions/` or `STATUS.yaml`
    as defeating its ruling. This is not that commit - the probe used a different
    excluded path - but it is the mechanism that would produce it, and the record
    should be read as having been reachable rather than as having been defeated.
    An earlier version of this docstring said 0064 named this case; a witness
    checked the record and it does not.

    The graded set is now this range plus whatever is about to be staged. Staging
    still follows `--path` alone; a path already committed needs no `git add`,
    and adding one would sweep in whatever is dirty there.
    """
    try:
        out = _git("diff", "--name-only", f"{target}...{branch}")
    except RuntimeError as exc:
        raise LandingRefused(
            f"cannot compute what a merge onto {target} would carry: {exc}. Until that "
            "range is readable the gate cannot know what it is grading, so it refuses "
            "rather than grading the staged paths alone.") from exc
    return [line.strip() for line in out.splitlines() if line.strip()]


def _commit_span(target: str, branch: str) -> tuple[int, int]:
    """How many commits the branch is ahead of and behind the target."""
    counts = _git("rev-list", "--left-right", "--count", f"{target}...{branch}").split()
    return int(counts[1]), int(counts[0])


def repo_relative(raw: str) -> str:
    """Express one path the way a grant's scope prefixes are written.

    A grant declares repository-relative prefixes such as `scripts/`, and a
    worker reporting what it changed may well hand back an absolute path. The
    first `sov-loop` run did exactly that, and every absolute path would have
    failed the scope check for the wrong reason - not because the grant refused
    the file, but because the two were never comparable.

    Every path is resolved, relative ones included, before it is compared. A
    relative path is not automatically inside the repository: `scripts/../STATUS.yaml`
    begins with an admitted prefix and names an excluded file, and an earlier
    version of this function that skipped `resolve()` for relative paths admitted
    it. So did `scripts/../decisions/`, and `scripts/../contracts/standing-grants.json`,
    which is the grant rewriting itself. A witness found all three before the
    grant was live.

    A path that resolves under the repository root comes back relative to it. One
    that resolves outside comes back absolute, so it fails the scope check rather
    than being quietly rewritten into scope.

    A trailing separator survives, because `Path` drops it and the boundary reads
    it as meaning. `contracts/` names a directory and the evaluator refuses it;
    dropping the separator produced `contracts`, which the evaluator admitted
    while `git add` staged the grant registry with it. Canonicalising must never
    turn a refusal into a pass, and `git status --porcelain` reports an untracked
    directory with exactly that trailing slash, so this arrives without an
    adversary.
    """
    trailing = "/" if raw.rstrip().endswith(("/", "\\")) else ""
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    resolved = candidate.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix() + trailing
    except ValueError:
        return resolved.as_posix() + trailing


def directory_paths(paths: list[str]) -> list[str]:
    """Of the paths named for staging, the ones that are directories on disk.

    `git add -- contracts/sub` stages every file beneath it, including files this
    landing never enumerated and files another session is holding. That is the
    blanket stage this module's own opening docstring refuses, spelled as one
    path. The evaluator cannot see it - it holds no filesystem - but the caller
    can, so the refusal belongs here.
    """
    return [p for p in paths if (ROOT / p).is_dir()]


def _held_elsewhere(paths: list[str]) -> list[str]:
    """Of the paths being landed, the ones another live session is holding.

    `sov_session.py contested` already answers this and already excludes the
    asking session, so the gate asks it rather than re-deriving who is who.
    """
    done = subprocess.run([sys.executable, "scripts/sov_session.py", "contested", "--json"],
                          cwd=ROOT, capture_output=True, text=True)
    if done.returncode != 0:
        return [f"could not read contested paths: {done.stderr.strip()}"]
    try:
        contested = json.loads(done.stdout or "[]")
    except json.JSONDecodeError:
        return ["could not parse the contested-path report"]
    # Containment in both directions. Equality hid a contested file inside a
    # named directory; asking only the one direction then hid the reverse, a
    # session holding `contracts/sub` while this landing stages
    # `contracts/sub/deep.json`. `sovsession/claims.py` records any repository
    # path without checking whether it is a file, so holding a subtree while
    # working in it is admissible and ordinary. Both readings are the same
    # collision and it does not matter which side spelled the directory.
    wanted = {repo_relative(p).rstrip("/") for p in paths}
    held = []
    for entry in contested:
        path = entry.get("path") if isinstance(entry, dict) else str(entry)
        seen = repo_relative(path or ".").rstrip("/")
        if any(seen == w or seen.startswith(w + "/") or w.startswith(seen + "/")
               for w in wanted):
            holder = entry.get("holder", "another session") if isinstance(entry, dict) else "?"
            held.append(f"{path}: held by {holder}")
    return held
