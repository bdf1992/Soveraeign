"""Load `contracts/counted-populations.json` and derive what each population holds.

Two referents, split the way `scripts/sovsnapshot/claims.py` splits them and for
the same reason. A population counted out of the filesystem is counted out of the
commit at HEAD, because Bdo's ruling on acceptance packet A5 established that a
committed page states counts of committed state - and because globbing the working
tree let one untracked directory belonging to a sibling session turn a required
gate red for everyone on the branch. A population the repository already computes
is read where the repository computes it, because re-deriving it here would be the
second implementation that got an earlier check nine conformance cases against the
suite's own twenty.

Every derivation may fail, and failing is not the same as a number being wrong. A
missing source, an unreadable projection, or a checkout too shallow to answer
raises `Underivable`, which the grader reports as "this environment cannot settle
this claim" rather than as drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import fnmatch
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contracts" / "counted-populations.json"


class Underivable(Exception):
    """The source cannot answer here. Not drift, and never graded as drift."""


@dataclass(frozen=True)
class Population:
    """One countable population, its anchors, and where a claim about it binds."""

    id: str
    counts: str
    derivation: dict
    anchors: tuple[str, ...]
    scoped_anchors: tuple[str, ...] = ()
    scope: tuple[str, ...] = ()

    def binds(self, path: str, anchor: str) -> bool:
        """Whether a claim at `path` using `anchor` is a claim about this population.

        Scope restricts the scoped anchors and only those. An unscoped anchor is
        declared because its wording names this population and can name nothing
        else - `declared Record operations` says which manifest it means - so it
        binds wherever it is written. Applying scope to both kinds was this
        module's first defect: `.claude/epic/NARRATIVE.md` counted the Record
        Service's operations by name, outside `services/record/`, and went
        ungraded while stale.
        """
        if anchor in self.scoped_anchors:
            return any(path.startswith(prefix) for prefix in self.scope)
        return True


def contract() -> dict:
    """The declaration itself, which is the only place a population is named."""
    try:
        return json.loads(CONTRACT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as broken:
        raise Underivable(f"the counted-populations contract is unreadable: {broken}") from broken


def _committed_paths() -> list[str]:
    """Every path the commit at HEAD holds.

    A shallow or absent checkout raises rather than answering zero. Answering zero
    would report every count in the repository as drifted against an empty record,
    which is the failure mode that made three CI workflows red against a page that
    was correct.
    """
    try:
        listed = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError) as missing:
        raise Underivable(f"the committed file list is unavailable: {missing}") from missing
    paths = [line for line in listed.stdout.splitlines() if line]
    if not paths:
        raise Underivable("the commit holds no listed files, so nothing can be counted")
    return paths


def _files(derivation: dict, paths: list[str]) -> int:
    excluded = set(derivation.get("exclude", ()))
    return len([p for p in paths
                if fnmatch.fnmatch(p, derivation["glob"]) and p not in excluded])


def _dirs(derivation: dict, paths: list[str]) -> int:
    """Directories the commit holds, which git records only through the files in them."""
    glob = derivation["glob"]
    depth = glob.count("/") + 1
    found = set()
    for path in paths:
        parts = path.split("/")
        if len(parts) <= depth:
            continue
        candidate = "/".join(parts[:depth])
        if fnmatch.fnmatch(candidate, glob):
            found.add(candidate)
    return len(found)


def _json_array(derivation: dict) -> int:
    """Read where the repository computes it, working tree and not commit."""
    document = ROOT / derivation["path"]
    if not document.is_file():
        raise Underivable(f"{derivation['path']} is absent")
    try:
        loaded = json.loads(document.read_text(encoding="utf-8"))
        return len(loaded[derivation["key"]])
    except (json.JSONDecodeError, KeyError, TypeError, OSError, UnicodeDecodeError) as broken:
        raise Underivable(f"{derivation['path']} is unreadable: {broken}") from broken


def _python_length(derivation: dict) -> int:
    """Import the table the repository already runs rather than re-deriving it."""
    if str(ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(ROOT / "scripts"))
    try:
        module = __import__(derivation["module"], fromlist=[derivation["name"]])
        return len(getattr(module, derivation["name"]))
    except (ImportError, SyntaxError, OSError, AttributeError, TypeError) as missing:
        # Narrow deliberately. A bare `except` here would swallow a defect in this
        # module and report it as a bad checkout.
        raise Underivable(f"{derivation['module']} could not be read: {missing}") from missing


def derive(derivation: dict, paths: list[str]) -> int:
    """Answer one derivation, or refuse to answer it."""
    kind = derivation.get("kind")
    if kind == "files":
        return _files(derivation, paths)
    if kind == "dirs":
        return _dirs(derivation, paths)
    if kind == "json_array":
        return _json_array(derivation)
    if kind == "python_length":
        return _python_length(derivation)
    raise Underivable(f"no derivation of kind {kind!r} exists")


def _expand(template: dict, paths: list[str]) -> list[Population]:
    """One template declaration over every member it finds, so adding a service
    adds its population without editing the contract.

    This is the difference between a contract and a list. A list of ten services
    goes short the day an eleventh is added, and nothing notices - which is the
    same defect this whole check exists to find.
    """
    members = sorted({
        "/".join(p.split("/")[:template["over"]["glob"].count("/") + 1])
        for p in paths
        if fnmatch.fnmatch("/".join(p.split("/")[:template["over"]["glob"].count("/") + 1]),
                           template["over"]["glob"])
        and len(p.split("/")) > template["over"]["glob"].count("/") + 1
    })
    built = []
    for member in members:
        name = member.split("/")[-1]
        fields = {"name": name, "Name": name.capitalize()}
        derivation = dict(template["derivation"])
        derivation["path"] = derivation["path"].format(**fields)
        if not (ROOT / derivation["path"]).is_file():
            continue
        built.append(Population(
            id=f"{template['id']}:{name}",
            counts=f"{template['counts']} ({name})",
            derivation=derivation,
            anchors=tuple(a.format(**fields) for a in template.get("anchors", ())),
            scoped_anchors=tuple(template.get("scoped_anchors", ())),
            scope=tuple(s.format(**fields) for s in template.get("scope", ())),
        ))
    return built


def load() -> tuple[list[Population], list[str]]:
    """Every declared population, expanded, with the committed path list it read."""
    declared = contract()
    paths = _committed_paths()
    populations = [
        Population(
            id=entry["id"],
            counts=entry["counts"],
            derivation=entry["derivation"],
            anchors=tuple(entry.get("anchors", ())),
            scoped_anchors=tuple(entry.get("scoped_anchors", ())),
            scope=tuple(entry.get("scope", ())),
        )
        for entry in declared["populations"]
    ]
    for template in declared.get("templates", ()):
        populations.extend(_expand(template, paths))
    return populations, paths
