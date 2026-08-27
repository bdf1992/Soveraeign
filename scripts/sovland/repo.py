"""What git says: branches, ranges, trackedness, and the object ids it would store.

Split out of `tree.py` on 2026-08-25 at the 300-line budget. Everything here
shells git and answers questions only git can answer - whether a path is tracked,
what a merge range contains, what object id the index holds. `tree.py` next door
answers what the working tree is, which is a different question and was twice the
source of a defect where one of the two learned about a new kind of path and the
other did not.

`ROOT` lives here because every git call needs it, and `tree.py` reads it through
this module rather than keeping a second copy - so a test that redirects the
repository redirects both.
"""

from __future__ import annotations

from pathlib import Path
import subprocess

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


def tracked(path: str) -> bool:
    """Whether git has this path in its index, which decides what `git add` does.

    A deleted tracked path and a path that never existed look identical on disk
    and behave oppositely: `git add` stages the removal for the first and exits
    128 for the second.
    """
    done = subprocess.run(["git", "ls-files", "--error-unmatch", "--", path],
                          cwd=ROOT, capture_output=True, text=True)
    return done.returncode == 0


def index_blob(path: str) -> str:
    """The object id git has staged for this path, or `deleted` if it staged a removal."""
    done = subprocess.run(["git", "rev-parse", f":{path}"], cwd=ROOT,
                          capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 else "deleted"


def worktree_blob(path: str) -> str:
    """The object id this path's working-tree bytes would become if staged now.

    `git hash-object --path` applies the same `.gitattributes` filters git applies
    when writing the index, which a raw sha256 does not. Without that, a
    normalising attribute makes disk bytes and index bytes differ legitimately and
    every landing would refuse. This repository pins LF so the two agree here, but
    that is a property of this repository rather than of git.
    """
    target = ROOT / path
    if target.is_symlink():
        # Mirror `fingerprint`'s ordering. is_file() follows the link and hashes
        # what it points at; git stages mode 120000 with the link target string
        # as the blob, so the two could never agree and every landing naming a
        # symlink refused permanently. A witness found this one round after the
        # same shape broke deletions: a new state taught to one reader of the
        # tree and not the other.
        done = subprocess.run(["git", "hash-object", "--stdin"], cwd=ROOT, input=str(
            target.readlink()).replace(chr(92), "/"), capture_output=True, text=True)
        return done.stdout.strip() if done.returncode == 0 else "unreadable"
    if not target.is_file():
        return "deleted"
    done = subprocess.run(["git", "hash-object", "--path", path, "--", str(target)],
                          cwd=ROOT, capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 else "unreadable"
