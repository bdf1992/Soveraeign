"""The commit at HEAD, which is the record the orientation page describes.

Bdo accepted acceptance packet A5 on 2026-08-26 and ruled the snapshot's referent
with it: `CLAUDE.md` is a committed artifact that every launched agent reads out
of a checkout, so the counts it states are counts of committed state. Before that
ruling every file-derived claim globbed the working tree, and one untracked
directory - a sibling session mid-creation of something unrelated - turned the
required gate red on an unmoved HEAD and printed an instruction to correct
`CLAUDE.md`, a file `grant:standing-landing-loop` excludes from its scope. The
gate demanded an edit no automated participant was permitted to make.

Everything in this module reads git and nothing in it reads the working tree. The
one source that deliberately stays on disk is the page itself, in
`claims.page_text`: someone correcting a number has to be graded on the number
they just wrote, not on the one still in the commit. That asymmetry is the whole
design - the page is the thing under test, the commit is what it is tested
against.

The ruling runs the other way too, and this is not softened. A counted source
added and the page corrected in the same uncommitted change is reported as drift
until the two land together, because until then the page states something the
record does not hold. `sov_snapshot.cmd_check` names the commit in that message
so a reader can tell which of the two is behind.

A source that cannot answer is never an answer of zero. Git absent from PATH, a
directory that is not a repository, an unborn HEAD, a path with nothing tracked
under it: each raises `Underivable`, which the grader reports as a fact about this
environment rather than about the page. There is deliberately no fall back to a
working-tree read when git is unavailable, because a silent fallback is the defect
the ruling closes wearing a guard.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, NamedTuple
import ast
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


def _git(*argv: str) -> subprocess.CompletedProcess[bytes]:
    """Run git rooted at `ROOT`, capturing bytes.

    Bytes rather than `text=True`: git path output is bytes, `-z` deliberately
    leaves it unquoted, and a name outside the process locale's encoding would
    raise or silently mangle under text mode. Every call site below decodes
    explicitly and says which errors handler it chose.
    """
    try:
        return subprocess.run(["git", *argv], cwd=ROOT, capture_output=True)
    except OSError as unavailable:
        # git missing from PATH, or ROOT not a directory. Before the referent
        # ruling `commits` was the only caller and let this escape as a traceback;
        # nine more claims reach git now, so an environment without it has to
        # refuse like any other source that cannot answer.
        raise Underivable(f"git could not be run here: {unavailable}") from unavailable


def _refused(done: subprocess.CompletedProcess[bytes], what: str) -> Underivable:
    """A failed git call, carrying git's own first line rather than a guess at why.

    Git already distinguishes "not a repository" from "path does not exist in
    HEAD" from "not a valid object name"; re-classifying those here would be a
    second, worse implementation of a message git writes correctly.
    """
    said = done.stderr.decode("utf-8", "replace").strip().splitlines()
    return Underivable(f"{what}: {said[0] if said else 'git failed and said nothing'}")


#: The listing held still for the span of one derivation pass, innermost last, and
#: `None` until that pass first asks for it. Empty outside a pass.
_HELD: list[list[str] | None] = []


@contextlib.contextmanager
def one_reading() -> Iterator[None]:
    """Read the commit's path list once and give every claim in this pass that answer.

    Seven of the ten claims ask for the same listing, so without this a single pass
    spawns seven git processes inside a gate whose wall time is graded - and the
    seven can disagree with each other if HEAD moves between them, which reports the
    check as broken when the record has simply moved.

    Held for the span of a pass and not for the process. A caller that runs two
    passes across a commit has to see the second one, and the fixture in
    `scripts/tests/test_sov_snapshot.py` is exactly that caller: it derives, lands a
    commit, and derives again expecting different numbers. A cache keyed on the
    process would pass every other case in this file and fail that one.

    The listing is filled lazily rather than on entry, so a git that cannot answer
    still refuses claim by claim and `derive_all` records a reason for each instead
    of dying on the way in.
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
    answer does not depend on where git was standing. `surrogateescape` so a path
    that is not valid UTF-8 survives to be matched rather than raising out of a
    counter - it cannot match an ASCII pattern either way, but refusing to decode
    it would take the other 981 paths down with it.
    """
    if _HELD and _HELD[-1] is not None:
        return _HELD[-1]
    done = _git("ls-tree", "-r", "-z", "--full-name", "--name-only", "HEAD")
    if done.returncode != 0:
        raise _refused(done, "the commit at HEAD could not be listed")
    paths = [raw.decode("utf-8", "surrogateescape")
             for raw in done.stdout.split(b"\0") if raw]
    if _HELD:
        _HELD[-1] = paths
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
    some tracked path continues past it, and a blob exactly when one ends there.
    That equivalence is why the derivation is exact and not an approximation.

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


def blob_text(path: str, what: str) -> str:
    """One committed file, decoded as UTF-8.

    Strict decoding here, unlike `tracked_paths`: this text is about to be parsed
    as JSON or as Python, and a replacement character would be parsed as content.
    """
    done = _git("show", f"HEAD:{path}")
    if done.returncode != 0:
        raise _refused(done, f"{what} could not be read from the commit at HEAD")
    try:
        return done.stdout.decode("utf-8")
    except UnicodeDecodeError as broken:
        raise Underivable(f"{what} at HEAD is not UTF-8: {broken}") from broken


def literal_length(path: str, name: str, what: str) -> int:
    """How many elements a committed module assigns to a plain tuple or list literal.

    This is the one derivation that reads committed source instead of counting
    committed files, and the objection it has to answer is on the record: an
    earlier proposal held that parsing a count out of HEAD would be a second
    implementation, the failure that made a draft count conformance cases as 9
    against the suite's own 20. The guard is that this refuses every shape it
    cannot count exactly - a comprehension, a concatenation, a name, a starred
    element, an absent assignment - so there is no shape where it can be
    confidently wrong. `scripts/tests/test_sov_snapshot.py` grades it against
    `len(CHECKS)` from the import on identical bytes, which is the evidence that
    it is the same count and not a second one.

    Every refusal below opens with the same `{what} could not be read`, and so does
    the one `blob_text` raises. An earlier round guaranteed that phrase by wrapping
    this function's exception at the call site, which produced "the check table
    could not be read: the check table could not be read from the commit at HEAD" -
    a stutter that appeared only when the messages were read rather than reasoned
    about.
    """
    unreadable = f"{what} could not be read"
    try:
        module = ast.parse(blob_text(path, what), filename=path)
    except SyntaxError as broken:
        raise Underivable(f"{unreadable}: {path} at HEAD does not parse: "
                          f"{broken}") from broken
    for node in module.body:
        targets = node.targets if isinstance(node, ast.Assign) else (
            [node.target] if isinstance(node, ast.AnnAssign) else [])
        if not any(isinstance(t, ast.Name) and t.id == name for t in targets):
            continue
        if not isinstance(node.value, (ast.Tuple, ast.List)):
            raise Underivable(f"{unreadable}: {name} in {path} is a "
                              f"{type(node.value).__name__}, which has no length here")
        if any(isinstance(element, ast.Starred) for element in node.value.elts):
            raise Underivable(f"{unreadable}: {name} in {path} unpacks another "
                              "sequence, so its elements cannot be counted without "
                              "running it")
        return len(node.value.elts)
    raise Underivable(f"{unreadable}: {path} at HEAD assigns no module-level {name}")


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
    return int(done.stdout.decode("utf-8", "replace").strip())
