"""Settled experience under one root, read as the basis a candidate Definition may cite.

Experience is settled here in the repository's own sense and no looser one: a custody
member that an independent participant observed (`standing: WITNESSED`) and that landed
(`work_state: LANDED`). A member that is merely built has not been judged by anyone else,
and a member that is witnessed but unlanded settled nothing, so neither is basis.

Every address is resolved to bytes under `root` and digested. An address a member names
that is not present is reported as a defect rather than skipped, because a basis that
silently shrinks is what P15-Q4.1 is written against.

Three limits, stated because a reader would otherwise assume otherwise. The standing and the
work state are taken from the custody record itself; nothing here corroborates them, so a
member falsely written as settled is admitted. A directory member is digested from the files
under it that this repository's own `.gitignore` does not exclude, over a floor of generated
names for a root that declares none; the matcher implements the subset of ignore syntax this
repository uses, not git's whole grammar. And in the live path the addresses gathered
here are both the basis and what the candidate cites, so P15-Q4.1 grades whether synthesis
preserved what it was given, not whether the gathering was right. That the predicate can
fail at all is proved by the fixture's `basis-dropped` and `no-sources` variants, not by
the live reading.
"""

from __future__ import annotations

from fnmatch import fnmatch
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any
import json

CUSTODY_COLLECTION = "contracts/custodies/phase-1-5.json"
LANDED = "LANDED"
SETTLED_STANDINGS = ("WITNESSED", "RATIFIED")
"""Standings that mean an independent participant has judged the member. `RATIFIED` is
above `WITNESSED` on the lifecycle, so admitting only the exact token `WITNESSED` would
silently drop a member that a seat had since settled. Compared as whole tokens, never as
substrings: `NOT_WITNESSED` contains `WITNESSED` (`CLAUDE.md`, trap T3). The fixture carries
a `NOT_WITNESSED` member for that reason, and the self-check refuses a reading that cites
it; a sixth witness pointed out that the rule was asserted here with nothing proving it."""


IGNORE_DECLARATION = ".gitignore"
"""Where this repository says which bytes it does not keep.

A ninth witness found that a directory member was digested from every file beneath it, so
importing the service wrote bytecode and the candidate's identity moved: three clean
checkouts of one commit produced three different proposal ids, and a fourth appeared after
running the repository's own verification command. The first repair excluded a hand-written
list of generated names, and a tenth witness showed that list was a third declaration of
"generated" in this repository, agreeing with neither `.gitignore` nor `scripts/lint.py`:
six ordinary ignored forms it missed - an editor swap file, a local database, a log, an
egg-info directory, a coverage file, a `.DS_Store` - each moved the digest.

So the declaration is read rather than restated. `.gitignore` is a tracked file and needs no
git to open. What is implemented is the subset of its syntax this repository uses: a
directory pattern ending in `/`, a glob, a plain name, and a `!` negation. A path-bearing
pattern is matched against the member-relative path as well as the name. That is not git's
own matching, and the difference does not all run one way: an unanchored pattern matches at
any depth as git's does, a directory pattern matches only directories, and an anchored or
`**` pattern is not implemented. This repository's declaration uses none of the last."""

GENERATED_DIRS = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
                            ".ipynb_checkpoints", ".tox", ".venv", "node_modules"})
"""A floor under the declaration, for a root whose `.gitignore` is absent or unreadable."""

GENERATED_SUFFIXES = frozenset({".pyc", ".pyo", ".pyd"})
"""File suffixes of the same kind."""


def _ignore_patterns(root: Path) -> tuple[list[str], list[str]]:
    """The ignore and negation patterns this repository declares.

    A pattern ending in `/` names a directory and is kept apart from the rest, because a
    directory pattern must not match a file of the same name. An eleventh witness measured
    the first version of this against `git check-ignore` over controlled paths and found it
    excluding nine paths git keeps - a file called `build`, one called `dist`, one called
    `env` - because every trailing slash had been stripped away. The docstring at the time
    warned that the matcher was narrower than git; it was broader, in the direction that
    quietly drops content out of a member's digest.
    """
    try:
        text = (root / IGNORE_DECLARATION).read_text(encoding="utf-8")
    except OSError:
        return [], []
    ignore: list[str] = []
    negate: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        target = negate if stripped.startswith("!") else ignore
        pattern = stripped.lstrip("!")
        target.append(pattern if pattern.endswith("/") else pattern.strip("/"))
    return ignore, negate


def _matches(relative: PurePosixPath, patterns: list[str]) -> bool:
    """True when any pattern matches this member-relative path, a parent of it, or its name.

    A pattern ending in `/` is tested against the path's directory components alone, so
    `build/` excludes everything under a `build` directory and keeps a file named `build`.
    """
    parents = relative.parts[:-1]
    for pattern in patterns:
        if pattern.endswith("/"):
            if any(fnmatch(part, pattern[:-1]) for part in parents):
                return True
            continue
        if any(fnmatch(candidate, pattern)
               for candidate in (str(relative), relative.name, *relative.parts)):
            return True
    return False


def _is_artifact(entry: Path, base: Path, ignore: list[str], negate: list[str]) -> bool:
    """True when this file is content the repository keeps, rather than output a tool left.

    The floor applies whatever the declaration says, so a root with no `.gitignore` still
    refuses bytecode. Beyond it the repository's own declaration decides, and a negation in
    that declaration wins, which is what `!.env.example` is for.
    """
    relative = PurePosixPath(entry.relative_to(base).as_posix())
    if any(part in GENERATED_DIRS for part in relative.parts):
        return False
    if entry.suffix in GENERATED_SUFFIXES:
        return False
    if _matches(relative, negate):
        return True
    return not _matches(relative, ignore)


def digest(path: Path, root: Path | None = None) -> str | None:
    """The sha256 at `path`, or None when nothing is readable there.

    A directory digests as its tree: every file under it the repository keeps, in sorted
    relative-path order, each contributing its path and its bytes. A member whose address is
    a service is then pinned by what the service contains, not merely by the fact that a
    directory exists, and not by what a tool left there. `root` says where to read the ignore
    declaration; without it only the floor applies.

    Each contribution is length-framed. A tenth witness showed the unframed form was not
    injective: a member holding `ab` with empty contents and one holding `a` containing `b`
    digested identically, so "the identity is a function of the artifact" held in one
    direction only. Framing moved the live identity once, at the commit that introduced it.
    """
    if path.is_dir():
        ignore, negate = _ignore_patterns(root) if root is not None else ([], [])
        rolling = sha256()
        for entry in sorted(path.rglob("*")):
            if not entry.is_file() or not _is_artifact(entry, path, ignore, negate):
                continue
            name = str(entry.relative_to(path)).replace("\\", "/").encode("utf-8")
            try:
                content = entry.read_bytes()
            except OSError:
                return None
            rolling.update(f"{len(name)}:".encode("ascii"))
            rolling.update(name)
            rolling.update(f"{len(content)}:".encode("ascii"))
            rolling.update(content)
        return rolling.hexdigest()
    try:
        return sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _members(collection: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Every member of every custody in the collection, paired with its clause."""
    pairs: list[tuple[str, dict[str, Any]]] = []
    for custody in collection.get("custodies") or []:
        if not isinstance(custody, dict):
            continue
        clause = str(custody.get("exit_clause") or custody.get("custody_id") or "?")
        for member in custody.get("members") or []:
            if isinstance(member, dict):
                pairs.append((clause, member))
    return pairs


def gather(root: Path, collection_path: str = CUSTODY_COLLECTION) -> dict[str, Any]:
    """Read every settled member under `root`, digested at the address it declares.

    Returns the settled sources with their digests, the clauses they came from, and the
    defects found. No session or transcript is consulted, so a second participant reproduces
    it from a clean tree.

    It reads the working tree under `root`, not a git object. Earlier wording here said
    "committed files only", which a sixth witness disproved by appending one uncommitted byte
    to a settled member and watching the proposal identity move. Reproducibility therefore
    requires a clean tree, which is why every reading of this member has been taken at a
    frozen commit (`CLAUDE.md`, trap T6).
    """
    defects: list[str] = []
    try:
        collection = json.loads((root / collection_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as unreadable:
        return {"sources": [], "clauses": [], "defects": [f"{collection_path}: {unreadable}"],
                "collection": collection_path}
    sources: dict[str, dict[str, Any]] = {}
    clauses: set[str] = set()
    for clause, member in _members(collection):
        if member.get("standing") not in SETTLED_STANDINGS:
            continue
        if member.get("work_state") != LANDED:
            continue
        address = member.get("address")
        if not isinstance(address, str) or not address:
            defects.append(f"{clause}: a settled member declares no address")
            continue
        clauses.add(clause)
        found = digest(root / address, root)
        if found is None:
            defects.append(f"{clause}: the settled member {address} is not present")
            continue
        sources.setdefault(address, {"address": address, "digest": found, "clause": clause})
    return {
        "sources": [sources[key] for key in sorted(sources)],
        "clauses": sorted(clauses),
        "defects": defects,
        "collection": collection_path,
    }
