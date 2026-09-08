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

What this does and does not reach is declared in `contracts/harness-claims.json`,
not left to be inferred from a green run. Two kinds are derived from records and
generalize (CAPABILITY, REFERENCE, and STANDING within its one sentence form);
two cover exactly the vocabulary that contract lists (VOLATILE, RETIRED); one
checks presence only (PROVENANCE). A first version of this module graded only
`<subject>_status is <TOKEN>` and would have missed every prose defect the same
branch removed - "accepted but unbuilt", a refusal conditioned on a closed phase,
an identifier that no longer resolves. Those are now cases in `selfcheck`.

This does not lint prose. A description may say what it likes as long as its
assertions hold and it does not state standing, which is the one representation
rule the contract imposes and the remedy is always deletion.

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
STANDING_TOKEN = re.compile(r"\b([a-z][a-z0-9_]*_status) is ([A-Z][A-Z0-9_]+)")
FRONTMATTER_TOOLS = re.compile(r"^tools:\s*(.+)$", re.M)
DESCRIPTION = re.compile(r"^description:\s*(?:>-\s*\n)?((?:.*(?:\n(?:[ \t]+.*|))*))", re.M)


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


def _described(root: Path) -> list[Path]:
    """The two file kinds that carry a `description:` a participant discovers by."""
    return sorted((root / ".claude" / "skills").glob("*/SKILL.md")) + \
        sorted((root / ".claude" / "agents").glob("*.md"))


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
    """A tool named in agent frontmatter must be one a supported host provides."""
    contract = _contract(root, "harness-hosts.json")
    portable = set(contract["portable"])
    retired = contract.get("retired", {})
    defects = []
    for path in sorted((root / ".claude" / "agents").glob("*.md")):
        match = FRONTMATTER_TOOLS.search(path.read_text(encoding="utf-8"))
        if not match:
            continue
        for tool in (t.strip() for t in match.group(1).split(",")):
            if not tool or tool in portable:
                continue
            why = retired.get(tool) or f"not in the portable set: {sorted(portable)}"
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


@emits("VOLATILE")
def check_volatile(root: Path = ROOT) -> list[Defect]:
    """A description states what a skill is for, never what is built.

    Covers exactly the vocabulary `contracts/harness-claims.json` declares. This
    kind does not generalize and the contract says so: a new way of writing "not
    built yet" passes until it is added there.
    """
    contract = _contract(root, "harness-claims.json")
    terms = [(e["term"], e["why"]) for e in contract["standing_vocabulary"]]
    remedy = contract["representation_rule"]["remedy"]
    defects = []
    for path in _described(root):
        match = DESCRIPTION.search(path.read_text(encoding="utf-8"))
        if not match:
            continue
        text = " ".join(match.group(1).split()).lower()
        for term, why in terms:
            if term in text:
                defects.append(Defect("VOLATILE", f"{path.relative_to(root)} description says "
                                                  f"{term!r}", f"{why} {remedy}"))
    return defects


@emits("RETIRED")
def check_retired(root: Path = ROOT) -> list[Defect]:
    """An identifier cited in the harness must still resolve to a record."""
    contract = _contract(root, "harness-claims.json")
    defects = []
    for path in _harness_files(root):
        text = path.read_text(encoding="utf-8")
        for entry in contract["retired_identifiers"]:
            if entry["term"] in text:
                defects.append(Defect(
                    "RETIRED", f"{path.relative_to(root)} cites {entry['term']}",
                    f"{entry['why']} Use {entry['replacement']}."))
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
ALL_CHECKS = (check_capability, check_standing, check_reference, check_volatile,
              check_retired, check_provenance, check_selfclaim)


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
