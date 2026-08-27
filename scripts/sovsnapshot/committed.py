"""The commit at HEAD, which is the record the orientation page describes.

Bdo accepted acceptance packet A5 on 2026-08-26 and ruled the snapshot's referent
with it: `CLAUDE.md` is a committed artifact that every launched agent reads out
of a checkout, so the counts it states are counts of committed state. Before that
ruling every file-derived claim globbed the working tree, and one untracked
directory - a sibling session mid-creation of something unrelated - turned the
required gate red on an unmoved HEAD and printed an instruction to correct
`CLAUDE.md`, a file `grant:standing-landing-loop` excludes from its scope. The
gate demanded an edit no automated participant was permitted to make.

The ruling moved the six file-counting derivations and no more. It left
`verification checks` and `declared operations` where they were, because each
already reads a number the repository computes and pulling the same bytes out of
`git show HEAD:...` would be a second implementation of an existing count rather
than a change of referent. `claims.UNCHECKED` says which half is which.

Every count here is of the commit; no count here is of the working tree. Two
things in this module do touch the checkout and neither is a count: `ROOT` is
resolved from this file's own location, and git is run with the checkout as its
working directory. Three *sources* deliberately stay on disk and none of them is
read here - the page itself in `claims.page_text`, the check table, and the
capability map projection. The page is the one that makes the design asymmetric:
someone correcting a number has to be graded on the number they just wrote, not
on the one still in the commit. The page is the thing under test, the commit is
what it is tested against.

The ruling runs the other way too, and this is not softened. A counted source
added and the page corrected in the same uncommitted change is reported as drift
until the two land together, because until then the page states something the
record does not hold. `sov_snapshot.cmd_check` names the commit in that message
so a reader can tell which of the two is behind.

A source that cannot answer is never an answer of zero. Git absent from PATH, a
directory that is not a repository, an unborn HEAD, a path with nothing tracked
under it, git blocking past its timeout: each raises `Underivable`, which the
grader reports as a fact about this environment rather than about the page. No
function here falls back to a working-tree read when git is unavailable, because a
silent fallback is the defect the ruling closes wearing a guard. That is a
property of the code as written, checked by reading it and by the cases in
`scripts/tests/test_sov_snapshot.py`; `selfcheck.derivations_read_the_commit`
grades the shape of the claim table and does not prove the absence of a fallback,
and says so.

Two rules about shape are stated here because both are places the new derivation
can differ from the old glob, and neither has an instance in this repository:

- a leaf of the recursive listing is not a directory. A submodule and a symlink
  are leaves, so neither is counted by a `dirs=True` claim, where `Path.is_dir()`
  would have counted a checked-out submodule and would have counted a symlink or
  junction on a host that materialises one as a directory.
- a directory prefix is matched by exact case, like every other match here. This
  repository sets `core.ignorecase=true`, so git will record `Decisions/` if
  someone commits it, and this module would then see nothing under `decisions/`
  and refuse rather than miscount.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, NamedTuple
import contextlib
import fnmatch
import subprocess

#: The repository this check reports on, fixed by where this file sits rather than
#: by the process working directory. `verify.py` launches checks from several cwds
#: and several sessions run from worktrees, so a git call anchored on the caller's
#: cwd would answer about whichever repository the caller happened to stand in -
#: and would answer confidently, which is worse than failing.
ROOT = Path(__file__).resolve().parents[2]


class Underivable(Exception):
    """A source could not answer, which is a different fact from the page being wrong."""


class Entry(NamedTuple):
    """One direct child of a committed directory: its own name, and blob or tree."""

    name: str
    kind: str


#: How long any one git call may take before this stops waiting for it. A pass
#: now spawns three git processes where it spawned two, and a git blocked on an
#: index lock or a credential helper would hang the gate whose wall time is graded
#: - with no refusal, because a process that never returns never fails. Generous
#: against the measured cost: the slowest call here is a 25 ms full listing.
GIT_TIMEOUT_SECONDS = 30

#: The only argument vectors this module hands git. `_git` takes `*argv`, so the
#: subcommand is chosen at each call site and nothing above it read the vector: an
#: independent reading put `ls-files --others --exclude-standard --cached` into a
#: claim and got the original working-tree defect back, through a call the shape
#: guard approved for reaching `committed`. Reaching this module is not the
#: property that matters; running one of these is. The referent ruling is exactly
#: the gap between `ls-tree HEAD` and `ls-files`, so it is pinned rather than said.
PERMITTED_ARGV = frozenset({
    ("ls-tree", "-r", "-z", "--full-name", "--name-only", "HEAD"),
    ("rev-parse", "--is-shallow-repository"),
    ("rev-list", "--count", "HEAD"),
})


class NotADeclaredReading(Exception):
    """A git call this module does not declare.

    Deliberately not an `Underivable`: an environment that cannot answer is a
    refusal the check survives, while a vector nobody declared is a defect here,
    and reporting it as "cannot derive" would hide the one thing the referent
    ruling exists to fix. It propagates.
    """


def _git(*argv: str) -> subprocess.CompletedProcess[bytes]:
    """Run git rooted at `ROOT`, capturing bytes.

    Bytes rather than `text=True`: git path output is bytes, `-z` deliberately
    leaves it unquoted, and a name outside the process locale's encoding would
    raise or silently mangle under text mode. Every call site below decodes
    explicitly and says which errors handler it chose.
    """
    if tuple(argv) not in PERMITTED_ARGV:
        raise NotADeclaredReading(
            f"git {' '.join(argv)} is not a declared reading; adding one means "
            "declaring it in PERMITTED_ARGV with a case proving it reads the commit")
    try:
        return subprocess.run(["git", *argv], cwd=ROOT, capture_output=True,
                              timeout=GIT_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired, UnicodeEncodeError) as unavailable:
        # git missing from PATH, ROOT not a directory, git not returning, or an
        # argument holding a lone surrogate that Windows cannot pass to a process.
        # Before the referent ruling `commits` was the only caller and let all of
        # these escape as tracebacks; seven more claims reach git now, so an
        # environment that cannot run it has to refuse like any other source that
        # cannot answer.
        raise Underivable(f"git could not be run here: {unavailable}") from unavailable


def _refused(done: subprocess.CompletedProcess[bytes], what: str) -> Underivable:
    """A failed git call, carrying git's own first line rather than a guess at why.

    Git already distinguishes "not a repository" from "path does not exist in
    HEAD" from "not a valid object name"; re-classifying those here would be a
    second, worse implementation of a message git writes correctly.
    """
    said = done.stderr.decode("utf-8", "replace").strip().splitlines()
    return Underivable(f"{what}: {said[0] if said else 'git failed and said nothing'}")


#: The listing held still for the span of one derivation pass, innermost last, each
#: entry `None` until that pass first asks or `(repository, paths)` after. Empty
#: outside a pass. Single-threaded by assumption: `verify.py` runs its checks in a
#: thread pool but every check is a subprocess, so nothing shares this list today.
_HELD: list[tuple[str, list[str]] | None] = []


@contextlib.contextmanager
def one_reading() -> Iterator[None]:
    """Read the commit's path list once and give every claim in this pass that answer.

    Seven of the ten claims ask for the same listing, so without this a successful
    pass spawns seven git processes inside a gate whose wall time is graded - and
    the seven can disagree with each other if HEAD moves between them, which reports
    the check as broken when the record has simply moved. A failed listing is not
    held, so a pass against an unreachable git still makes the seven calls; holding
    a failure would let one transient error decide nine claims.

    Held for the span of a pass and not for the process, and keyed on the repository
    it was read from. A caller that runs two passes across a commit has to see the
    second one, and the fixture in `scripts/tests/test_sov_snapshot.py` is exactly
    that caller: it derives, lands a commit, and derives again expecting different
    numbers. The key is what makes the hold safe rather than merely usually right -
    without it, `ROOT` moving inside a pass returned the previous repository's
    listing and answered confidently about the wrong tree.

    One pass, not one command: `sov_snapshot.cmd_check` derives twice, once to prove
    the grader works and once to grade the page, and those are two readings.
    """
    _HELD.append(None)
    try:
        yield
    finally:
        _HELD.pop()


def tracked_paths() -> list[str]:
    """Every path the commit at HEAD holds, repository-relative.

    `-z` because git C-quotes non-ASCII paths otherwise, which would turn one
    accented filename into a name that matches no pattern. `--full-name` so the
    answer does not depend on where git was standing. `surrogateescape` because a
    path that is not valid UTF-8 has to survive to be matched: the skills claim
    matches on `*`, which matches anything, so such a directory is genuinely part
    of that count - and refusing to decode one would take every other path in the
    listing down with it.
    """
    repository = str(ROOT)
    if _HELD and _HELD[-1] is not None and _HELD[-1][0] == repository:
        return _HELD[-1][1]
    done = _git("ls-tree", "-r", "-z", "--full-name", "--name-only", "HEAD")
    if done.returncode != 0:
        raise _refused(done, "the commit at HEAD could not be listed")
    paths = [raw.decode("utf-8", "surrogateescape")
             for raw in done.stdout.split(b"\0") if raw]
    if _HELD:
        _HELD[-1] = (repository, paths)
    return paths


def matches(path: str, pattern: str) -> bool:
    """Segment-wise fnmatch, so `*` never crosses a `/` the way `Path.glob` never did.

    A flat `fnmatch` over a whole path lets `services/*/contracts/service.json`
    match a manifest nested two directories deeper, which `Path.glob` would not
    have counted. `fnmatchcase` rather than `fnmatch`: the latter normalises case
    on Windows, and a check whose count depends on which platform ran it is
    telling you about the platform.
    """
    parts, globs = path.split("/"), pattern.split("/")
    return len(parts) == len(globs) and all(
        fnmatch.fnmatchcase(part, glob) for part, glob in zip(parts, globs))


def entries(directory: str, what: str) -> list[Entry]:
    """The direct children of a committed directory, each named blob or tree.

    Derived from the recursive path list rather than a second `ls-tree` per
    directory: git records no empty tree, so `d/x` is a tree at HEAD exactly when
    some tracked path continues past it, and a leaf exactly when one ends there.
    That equivalence is exact for the ordinary file, and the module docstring
    states where it is a rule rather than an equivalence: a submodule and a symlink
    are leaves here and are therefore not directories, which is a deliberate answer
    and not the same one `Path.is_dir()` gave on every host.

    Nothing tracked under the directory is `Underivable`, never zero. A missing
    `decisions/` once counted as zero, which turns "I cannot see the record" into
    a claim that the page is wrong by the whole count.
    """
    prefix = directory.rstrip("/") + "/"
    kinds: dict[str, str] = {}
    for path in tracked_paths():
        if not path.startswith(prefix):
            continue
        head, sep, _ = path[len(prefix):].partition("/")
        kinds[head] = "tree" if sep else "blob"
    if not kinds:
        raise Underivable(f"{what} cannot be counted: the commit at HEAD tracks "
                          f"nothing under {prefix}")
    return [Entry(name, kind) for name, kind in kinds.items()]


def count(directory: str, pattern: str, what: str, *, dirs: bool = False) -> int:
    """How many direct children of a committed directory match, by name and by kind."""
    wanted = "tree" if dirs else "blob"
    return len([e for e in entries(directory, what)
                if e.kind == wanted and matches(e.name, pattern)])


def count_paths(directory: str, pattern: str, what: str) -> int:
    """How many committed files under a directory match a whole repository-relative path.

    For a claim whose shape spans more than one directory level, where counting
    direct children says nothing.
    """
    under = [path for path in tracked_paths() if path.startswith(directory.rstrip("/") + "/")]
    if not under:
        raise Underivable(f"{what} cannot be counted: the commit at HEAD tracks "
                          f"nothing under {directory.rstrip('/')}/")
    return len([path for path in under if matches(path, pattern)])


def commits() -> int:
    """How many commits the history holds, when the history is all present.

    A shallow checkout answers this confidently and wrongly. `actions/checkout@v4`
    defaults to depth 1 and three workflows in `.github/` run `verify.py` after
    it, so in CI this reads 1 against a page stating hundreds and reports the page
    as drifted. That is the environment the required command runs in, and it
    genuinely cannot answer the question, so it says so. Every other claim here
    survives a shallow clone: the tree at HEAD is whole even at depth 1.
    """
    shallow = _git("rev-parse", "--is-shallow-repository")
    if shallow.returncode == 0 and shallow.stdout.strip() == b"true":
        raise Underivable("the checkout is shallow, so the commit count here is the "
                          "clone's depth rather than the repository's history")
    done = _git("rev-list", "--count", "HEAD")
    if done.returncode != 0:
        raise _refused(done, "the commit count could not be read")
    counted = done.stdout.decode("utf-8", "replace").strip()
    try:
        return int(counted)
    except ValueError as unreadable:
        # git exiting 0 and saying nothing countable. Unguarded this raised
        # `ValueError` straight through `derive_all`, which catches `Underivable`
        # only - a traceback out of the check, from the one function the module
        # docstring uses as its example of refusing properly.
        raise Underivable(f"the commit count could not be read: git exited 0 and said "
                          f"{counted!r}") from unreadable
