#!/usr/bin/env python3
"""Grade what the harness asserts against the records that own those claims.

`.claude/` is discovery surface. An agent definition, a skill description and a
workflow prompt are all read by a participant that has no other context, and each
one makes claims: this host provides that tool, that service is in this state,
this path holds the thing you want. Every other claim surface here is graded -
`sov_snapshot.py` re-derives the orientation numbers, `sov_traps.py` fails when a
trap stops being true, `sov_status_claims.py` types STATUS.yaml - and the harness
was the surface with no grader, which is why four agent definitions declared a
tool no invocation grants and a workflow prompt told launched agents a service
standing STATUS.yaml contradicts.

What this does and does not reach is declared in `contracts/harness-claims.json`.
Every kind here compares an extracted claim against a record that owns it, so
each generalizes: an unknown tool, an address nobody anticipated, an invented
status token and a subject STATUS.yaml never had are all refused without being
listed anywhere.

Two further kinds lived here and were withdrawn. VOLATILE and RETIRED matched a
hand-written list of nine strings, so "accepted but unbuilt" was refused while
"implementation is still pending" passed - the same claim, differently worded.
That is Red work, not Blue: SDLC.md puts generative detection in the adversarial
lane and declared cases in this one, and a phrase list is a declared case
pretending to be a net. `qa-lanes.yml` already carries a generative red lane for
it, gated off. Detecting a standing claim in arbitrary prose belongs there, and
what belongs here is whatever that lane lands as a fixture.

This does not lint prose. A description may say what it likes as long as the
assertions it makes are true of the records that own them. Whether prose asserts
standing in words nobody listed is not graded here at all; the contract's
`not_covered` says so and names the lane it belongs to.

STATUS.yaml is read line by line, never through a YAML parser. Eight subjects
carry two typed claims under one key, ruled legitimate by `sov_status_claims.py`;
a parser keeps only the last and would report the earlier claim as false.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
import subprocess
import sys

from sovharness import emits

ROOT = Path(__file__).resolve().parent.parent

#: Read but not graded. Drafts record what was true when written; grading them
#: would demand edits to the record of a past state.
EXEMPT_DIRS = ("drafts",)

#: Runtime state, gitignored by design: a scheduled run's ledger, a board survey's
#: batch. Absent in a clean checkout is correct, so naming one is not a dead address.
RUNTIME_PREFIXES = (".local/",)

PATH_TOKEN = re.compile(r"`((?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.[A-Za-z0-9]+)`")
#: A status claim, however it is punctuated. Widening this changes what is
#: extracted, never what counts as true - STATUS.yaml stays the oracle. That is
#: the line between this and the withdrawn kinds, whose word lists were
#: themselves the standard. A witness sized the old form at one spelling of six.
STANDING_TOKEN = re.compile(
    r"\b([a-z][a-z0-9_]*_status)\s*(?:is\s+(?:now\s+)?|[:=]\s*)([A-Z][A-Z0-9_]{2,})")
FRONTMATTER_TOOLS = re.compile(r"^tools:\s*(.+)$", re.M)


@dataclass(frozen=True)
class Defect:
    """One harness claim that its owning record does not support."""

    kind: str
    where: str
    detail: str

    def __str__(self) -> str:
        return f"{self.kind:<11} {self.where}\n            {self.detail}"


def _contract(root: Path, name: str) -> dict:
    return json.loads((root / "contracts" / name).read_text(encoding="utf-8"))


def _harness_files(root: Path = ROOT) -> list[Path]:
    """Every graded file under .claude/, drafts excluded."""
    harness = root / ".claude"
    out = []
    for path in sorted(harness.rglob("*")):
        if not path.is_file() or path.suffix not in (".md", ".js", ".json"):
            continue
        if any(part in EXEMPT_DIRS for part in path.relative_to(harness).parts):
            continue
        out.append(path)
    return out


def _status_claims(root: Path = ROOT) -> dict[str, set[str]]:
    """Every `<subject>_status: <TOKEN>` in STATUS.yaml, read line by line.

    A subject maps to the set of every value declared for it, not to one value:
    eight subjects legitimately carry two claims of different kinds under one key.
    """
    claims: dict[str, set[str]] = {}
    for line in (root / "STATUS.yaml").read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*([a-z][a-z0-9_]*_status):\s*(\S+)", line)
        if match:
            claims.setdefault(match.group(1), set()).add(match.group(2))
    return claims


@emits("CAPABILITY")
def check_capability(root: Path = ROOT) -> list[Defect]:
    """A tool named in agent frontmatter must be provided by a declared environment.

    Admissibility, not availability. A non-portable tool is admissible: an agent
    definition is loaded on whichever host runs it, and a name that host does not
    provide is inert there rather than an error. Refusing a non-portable name is
    how v1 of this check deleted PowerShell from four definitions on the evidence
    of one container, which cost the workstation environment a real capability.
    """
    contract = _contract(root, "harness-hosts.json")
    admissible = set(contract["admissible"])
    portable = set(contract["portable"])
    corrections = contract.get("corrections", {})
    defects = []
    for path in sorted((root / ".claude" / "agents").glob("*.md")):
        match = FRONTMATTER_TOOLS.search(path.read_text(encoding="utf-8"))
        if not match:
            continue
        for tool in (t.strip() for t in match.group(1).split(",")):
            if not tool or tool in admissible:
                continue
            why = corrections.get(tool) or (
                f"no declared environment provides it: "
                f"{sorted(contract['environments'])}")
            defects.append(Defect("CAPABILITY", f"{path.relative_to(root)} declares {tool!r}", why))
    return defects


@emits("STANDING")
def check_standing(root: Path = ROOT) -> list[Defect]:
    """A standing token asserted in the harness must be one STATUS.yaml declares."""
    claims = _status_claims(root)
    defects = []
    for path in _harness_files(root):
        for subject, asserted in STANDING_TOKEN.findall(path.read_text(encoding="utf-8")):
            declared = claims.get(subject)
            if declared is None:
                defects.append(Defect("STANDING", f"{path.relative_to(root)} asserts {subject}",
                                      "STATUS.yaml declares no such subject"))
            elif asserted not in declared:
                defects.append(Defect(
                    "STANDING", f"{path.relative_to(root)} says {subject} is {asserted}",
                    f"STATUS.yaml declares {' and '.join(sorted(declared))}"))
    return defects


def _roots(root: Path) -> list[Path]:
    """The places prose legitimately names a path from.

    Explicit, and only these. An earlier rule accepted an address if any file
    anywhere in the tree ended with it, which let an untracked cache or an
    archived copy validate `contracts/missing.json`. Breadth there is not
    generosity; it is the check declining to fail.
    """
    return [root, root / ".claude", *sorted(p for p in (root / "services").glob("*") if p.is_dir())]


def _tracked(root: Path) -> set[str] | None:
    """Git's index, or None outside a repository. Untracked files never validate."""
    try:
        out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True,
                             text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return set(out.split())


@emits("REFERENCE")
def check_reference(root: Path = ROOT) -> list[Defect]:
    """A repository address named in an orientation surface must resolve."""
    tracked = _tracked(root)
    bases = _roots(root)

    def resolves(ref: str, origin: Path) -> bool:
        for base in [origin.parent, *bases]:
            try:
                rel = str((base / ref).resolve().relative_to(root)).replace("\\", "/")
            except ValueError:
                continue
            if (rel in tracked) if tracked is not None else (root / rel).exists():
                return True
        return False

    defects = []
    for path in [root / "CLAUDE.md", *_harness_files(root)]:
        if not path.exists():
            continue
        for ref in sorted(set(PATH_TOKEN.findall(path.read_text(encoding="utf-8")))):
            if ref.startswith(("http", "~")) or ref.startswith(RUNTIME_PREFIXES):
                continue
            if not resolves(ref, path):
                defects.append(Defect("REFERENCE", f"{path.relative_to(root)} names {ref}",
                                      "resolves from no declared root, and is not tracked"))
    return defects




@emits("PROVENANCE")
def check_provenance(root: Path = ROOT) -> list[Defect]:
    """A skill vendored from another repository must declare where it came from."""
    from sovharness.provenance import missing_fields
    return [Defect("PROVENANCE", f"{path} is vendored",
                   f"declares no {', '.join(fields)}; a copy without a source is a fork")
            for path, fields in missing_fields(root)]


@emits("SELFCLAIM")
def check_selfclaim(root: Path = ROOT) -> list[Defect]:
    """The coverage contract must describe the kinds this module actually runs."""
    from sovharness.contract import check_contract
    return [Defect("SELFCLAIM", where, detail)
            for where, detail in check_contract(root, KINDS)]


#: Every kind this module runs. Each member was bound to its kind by @emits at
#: its own definition, so membership is the only thing this tuple decides.
ALL_CHECKS = (check_capability, check_standing, check_reference, check_provenance,
              check_selfclaim)


def kinds() -> set[str]:
    """The kinds this module actually runs, read off ALL_CHECKS membership."""
    return {check.kind for check in ALL_CHECKS}


KINDS = kinds()


def grade(root: Path = ROOT) -> list[Defect]:
    return [d for check in ALL_CHECKS for d in check(root)]


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "selfcheck":
        from sovharness.fixtures import selfcheck
        return selfcheck(grade, kinds())
    defects = grade()
    graded = len(_harness_files()) + 1
    if defects:
        print(f"harness claims: {len(defects)} defect(s) across {graded} graded files\n")
        for defect in defects:
            print(defect)
        print("\nEach line is a claim the harness makes that its owning record does not "
              "support. Repair the claim, or the record if the record is what is wrong.\n"
              "What this does and does not reach: contracts/harness-claims.json")
        return 1
    print(f"harness claims: {graded} files graded across {len(kinds())} kinds; coverage "
          f"and its limits are declared in contracts/harness-claims.json, which "
          f"SELFCLAIM grades against the kinds this module actually runs")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
