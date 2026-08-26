"""Decide whether a request path is one a grant's declared scope reaches.

Split out of `authority.py` on 2026-08-25, when five rounds of witness dissent
had grown this reasoning past the point where it was a detail of grant
evaluation. It answers one question - does this string name something inside the
scope and outside the exclusions - and the module next door answers whether the
grant is live, typed, timely and in budget.

Nothing here reads a file or knows a repository root. A caller canonicalises a
real path first (`scripts/sov_land.py`, `repo_relative`); this module refuses
anything it cannot compare rather than resolving it, which is what lets the
corpus in `conformance/fixtures/authority/grant-cases.json` grade it in an empty
directory.
"""

from __future__ import annotations

from typing import Iterable


def _normalise(path: str) -> str:
    """Compare repository paths in one direction of slash, whatever the host wrote."""
    cleaned = path.replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


#: A segment that does not name one child: `..` climbs, `.` stands still, and an
#: empty one comes from a doubled or trailing separator.
NON_NAMING_SEGMENTS = {"..", ".", ""}

#: Characters git reads as a pattern rather than as part of a filename. A path
#: carrying one names a set, and the set is chosen after the comparison is over.
PATTERN_CHARACTERS = "*?[]"

#: A leading colon opens git's pathspec magic, which rewrites what a string
#: selects before matching begins.
PATHSPEC_MAGIC = ":"


def _ungradeable(path: str) -> str | None:
    """Say why a string does not name exactly one repository-relative file.

    A grant declares repository-relative prefixes, so a prefix comparison is only
    honest about a string git will read as the same one file. Git transforms a
    pathspec in exactly two ways before it matches anything, and a string this
    check admits must survive both unchanged.

    It normalises. `scripts/../STATUS.yaml` begins with `scripts/` and is
    `STATUS.yaml`; `contracts/./standing-grants.json` and
    `contracts//standing-grants.json` do not begin with the excluded string and
    are the excluded file. A non-naming segment is what makes the string compare
    as something other than the path it names.

    It globs. `contracts/*` names no file at all until git expands it, which
    happens after the scope check has already decided. So does
    `contracts/standing-grants.jso?`, and so does a character class. A pattern is
    not a path that needs canonicalising; it is a set, and a set cannot be graded
    against a prefix at all.

    Each of those two classes was found by a witness against a version of this
    function that closed the previous one, which is why the test is now the
    property rather than the escapes anyone has thought of: literal, canonical,
    repository-relative, or it is not graded.

    The evaluator refuses rather than resolves. Resolving needs a repository root
    and a filesystem, and this module has neither on purpose - that is what lets
    its corpus grade it in an empty directory. A caller canonicalises first
    (`scripts/sov_land.py`, `repo_relative`), and a caller that does not gets a
    refusal instead of a pass, which is the direction a boundary check should
    fail in. Canonicalising cannot rescue a pattern: `repo_relative` returns
    `contracts/*` unchanged, because a glob has nothing to collapse.
    """
    cleaned = path.replace("\\", "/")
    if cleaned.startswith(PATHSPEC_MAGIC):
        return (f"{path} opens git's pathspec magic, which changes what the string selects "
                "after this check has read it")
    if cleaned.startswith("/") or (len(cleaned) > 1 and cleaned[1] == ":"):
        return (f"{path} is not repository-relative; a grant's scope is declared in "
                "repository-relative prefixes")
    found = next((c for c in PATTERN_CHARACTERS if c in cleaned), None)
    if found is not None:
        return (f"{path} carries the pattern character `{found}`, so it names a set that is "
                "chosen after this check has compared it")
    for segment in cleaned.split("/"):
        if segment in NON_NAMING_SEGMENTS:
            shown = f"`{segment}`" if segment else "an empty"
            return (f"{path} carries {shown} segment, so the string it is compared as is not "
                    "the path it names")
    return None


def _covers(prefixes: Iterable[str], path: str) -> str | None:
    """Return the first prefix that covers `path`, or None."""
    for prefix in prefixes:
        clean = _normalise(prefix)
        if path == clean.rstrip("/") or path.startswith(clean):
            return prefix
    return None


def _selects_excluded(excluded: Iterable[str], path: str) -> tuple[str, str] | None:
    """Return the first excluded entry a requested path selects, and how.

    Asked in both directions on purpose, because a path selects a file two ways.
    It can be that file or sit beneath it, which is the obvious reading. It can
    also be a directory that contains it: `contracts` is repository-relative,
    carries no pattern character and no non-naming segment, and
    `git add -- contracts` stages the grant registry.

    That is the one escape class that cannot be seen in the string. A directory
    names a set exactly as `contracts/*` does, but it is spelled entirely in
    segments that name things, so `_ungradeable` has nothing to object to. The
    question a scope check has to ask is not whether a string begins with an
    excluded prefix; it is whether the string selects something excluded.
    """
    for entry in excluded:
        bare = _normalise(entry).rstrip("/")
        if path == bare or path.startswith(bare + "/"):
            return entry, "is inside"
        if bare.startswith(path + "/"):
            return entry, "is a directory containing"
    return None


def out_of_scope(grant: dict, request: dict) -> str | None:
    """Name the first requested path the grant's scope does not reach."""
    scope = grant["scope"]
    included = scope.get("paths", ())
    excluded = scope.get("excluded_paths", ())
    for raw in request.get("paths", ()):
        ungradeable = _ungradeable(raw)
        if ungradeable is not None:
            return ungradeable
        path = _normalise(raw)
        selected = _selects_excluded(excluded, path)
        if selected is not None:
            entry, relation = selected
            if relation == "is inside":
                return f"{raw} is inside the excluded prefix {entry}"
            return f"{raw} is a directory containing the excluded {entry}"
        if _covers(included, path) is None:
            return f"{raw} is outside every path prefix the grant admits"
    return None

