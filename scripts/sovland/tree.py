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

from hashlib import sha256
from pathlib import Path
import json
import subprocess
import sys

from sovland import repo


def _run_check(name: str, argv: list[str]) -> str:
    """Run one repository check and reduce it to PASS or FAIL."""
    done = subprocess.run([sys.executable, *argv], cwd=repo.ROOT, capture_output=True, text=True)
    return "PASS" if done.returncode == 0 else "FAIL"


def gather_checks(skip: bool) -> dict[str, str]:
    """Run the checks the grant names as preconditions."""
    if skip:
        return {}
    return {
        "lint": _run_check("lint", ["scripts/lint.py"]),
        "verify": _run_check("verify", ["scripts/verify.py"]),
    }


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
        candidate = repo.ROOT / candidate
    resolved = candidate.resolve()
    try:
        return resolved.relative_to(repo.ROOT).as_posix() + trailing
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
    return [p for p in paths if (repo.ROOT / p).is_dir()]


def fingerprint(paths: list[str]) -> dict[str, str]:
    """What each path is right now: its bytes, or that it is a directory or absent.

    The gate grades a set and then stages it, and `gather_checks` runs `verify`
    and `lint` in between. Measured at twelve seconds. Everything graded is that
    stale by the time `git add` runs, and `git add` stages the bytes on disk then,
    not the bytes that were graded - so a file another session edits inside the
    window is committed under evidence that read the old content, in a working
    directory this repository expects several sessions to share.

    Taking a fingerprint at grade time and comparing it immediately before
    staging does not shrink the window. It makes the window fail closed: a
    landing whose evidence has stopped describing the tree refuses instead of
    committing something nobody graded.
    """
    seen: dict[str, str] = {}
    for path in paths:
        target = repo.ROOT / path
        if target.is_symlink():
            # Before is_file(), which follows the link and reads the target's
            # bytes. git stores a symlink as mode 120000 with the link target as
            # the blob, so hashing what it points at says "unchanged" about an
            # object whose kind changed.
            seen[path] = "symlink:" + str(target.readlink())
        elif target.is_dir():
            seen[path] = "directory"
        elif target.is_file():
            seen[path] = "sha256:" + sha256(target.read_bytes()).hexdigest()
        elif repo.tracked(path):
            # Deleted, but git knows it. `git add` on this exits 0 and stages the
            # removal, which is exactly right. An earlier version called this
            # `absent` alongside a path that never existed and refused both, so
            # the gate could not land a deletion at all.
            seen[path] = "deleted"
        else:
            seen[path] = "absent"
    return seen


def drifted(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Name every path whose fingerprint changed between grading and staging."""
    return sorted(p for p, was in before.items() if after.get(p) != was)


def staged_wrong(paths: list[str], graded_blobs: dict[str, str]) -> list[str]:
    """Paths whose staged object is not what was graded, read from the index itself.

    Comparing before `git add` narrows the stale-evidence window to one subprocess
    spawn; it does not close it. `git rev-parse :<path>` reads the index, which is
    precisely what the commit will contain, so comparing after staging and before
    committing closes it exactly. Nothing is committed at that point, so a
    mismatch costs a `git reset` and no effect has occurred.
    """
    return sorted(p for p in paths if repo.index_blob(p) != graded_blobs.get(p))


def absent_paths(fingerprints: dict[str, str]) -> list[str]:
    """Paths that never existed, which `git add` errors on rather than refusing.

    A predicate rather than an inline comprehension, so it can be tested for
    identity the way `directory_paths`, `drifted` and `staged_wrong` are. Six
    refusals in `cmd_land` all return 2, and asserting on printed prose couples a
    test to wording; asserting on the predicate does not.
    """
    return sorted(p for p, state in fingerprints.items() if state == "absent")


def _held_elsewhere(paths: list[str]) -> list[str]:
    """Of the paths being landed, the ones another live session is holding.

    `sov_session.py contested` already answers this and already excludes the
    asking session, so the gate asks it rather than re-deriving who is who.
    """
    done = subprocess.run([sys.executable, "scripts/sov_session.py", "contested", "--json"],
                          cwd=repo.ROOT, capture_output=True, text=True)
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
        if not path:
            # A claim record with no path resolved to the repository root through
            # the `or "."` fallback, and the whole-tree condition then blocked
            # every landing in the repository on one malformed record.
            continue
        seen = repo_relative(path).rstrip("/")
        # `repo_relative` normalises the repository root to `.`, and no ordinary
        # path starts with `./`, so a session holding the whole tree matched
        # nothing in either direction. Claiming everything is not ordinary use,
        # but it is recordable, and a collision check that misses the largest
        # possible claim is the wrong way round.
        if seen == "." or any(seen == w or seen.startswith(w + "/")
                              or w.startswith(seen + "/") for w in wanted):
            holder = entry.get("holder", "another session") if isinstance(entry, dict) else "?"
            held.append(f"{path}: held by {holder}")
    return held
