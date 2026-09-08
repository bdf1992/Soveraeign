#!/usr/bin/env python3
"""Grade what the harness asserts against the records that own those facts.

`.claude/` is discovery surface. An agent definition, a skill description and a
workflow prompt are all read by a participant that has no other context, and each
one makes claims: this host provides that tool, that service is in this state,
this path holds the thing you want. Every other claim surface in this repository
is graded - `sov_snapshot.py` re-derives the orientation numbers, `sov_traps.py`
fails when a trap stops being true, `sov_status_claims.py` types STATUS.yaml -
and the harness was the surface with no grader, which is why four agent
definitions declared a tool no invocation grants and a workflow prompt told
launched agents a service standing that STATUS.yaml contradicts.

Three claim kinds are graded, and only three, because each has an owning record
to be graded against:

  CAPABILITY  a tool named in agent frontmatter, against contracts/harness-hosts.json
  STANDING    `<subject>_status is <TOKEN>` asserted in .claude/, against STATUS.yaml
  REFERENCE   a repository path named in an orientation surface, against the tree
  PROVENANCE  a skill vendored from another repository, against its own declaration

This does not lint prose. A description may say whatever it likes as long as the
assertions it makes are true of the records that own them. Volatile-but-correct
claims pass today and fail the day they drift, which is the point: the check
holds what deletion cannot.

STATUS.yaml is read line by line, never through a YAML parser. Eight subjects
carry two typed claims under one key, ruled legitimate by `sov_status_claims.py`;
a parser keeps only the last and would report the earlier claim as false.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent

#: Read but not graded. Drafts and archived packets record what was true when
#: written; grading them would demand edits to the record of a past state.
EXEMPT_DIRS = ("drafts",)

#: Runtime state, gitignored by design. `.local/` is where a scheduled run writes
#: its ledger and a board survey its batch; absent in a clean checkout is correct,
#: so a reference to one is not a dead address.
RUNTIME_PREFIXES = (".local/",)

#: A path-shaped token in prose. Anchored on a repository-root-relative segment
#: so prose about `services/` in general is not mistaken for a file reference.
PATH_TOKEN = re.compile(r"`((?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.[A-Za-z0-9]+)`")
STANDING_TOKEN = re.compile(r"\b([a-z][a-z0-9_]*_status) is ([A-Z][A-Z0-9_]+)")
FRONTMATTER_TOOLS = re.compile(r"^tools:\s*(.+)$", re.M)


@dataclass(frozen=True)
class Defect:
    """One harness claim that its owning record does not support."""

    kind: str
    where: str
    detail: str

    def __str__(self) -> str:
        return f"{self.kind:<10} {self.where}\n           {self.detail}"


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

    A subject maps to the set of every value declared for it, not to one value.
    Eight subjects legitimately carry two claims of different kinds under one key
    (`scripts/sov_status_claims.py`); asserting either one is asserting something
    STATUS.yaml says.
    """
    claims: dict[str, set[str]] = {}
    for line in (root / "STATUS.yaml").read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*([a-z][a-z0-9_]*_status):\s*(\S+)", line)
        if match:
            claims.setdefault(match.group(1), set()).add(match.group(2))
    return claims


def check_capability(root: Path = ROOT) -> list[Defect]:
    """A tool named in agent frontmatter must be one a supported host provides."""
    contract = json.loads((root / "contracts" / "harness-hosts.json").read_text(encoding="utf-8"))
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
            why = retired.get(tool) or (
                f"not in contracts/harness-hosts.json portable set: {sorted(portable)}")
            defects.append(Defect("CAPABILITY", f"{path.relative_to(root)} declares {tool!r}", why))
    return defects


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


def _resolves(ref: str, origin: Path, suffixes: set[str], root: Path = ROOT) -> bool:
    """Does this address reach a file, read the way a participant would read it?

    Prose names a path from wherever the reader happens to be standing: from the
    repository root, from the document's own directory, or from the service the
    paragraph is about. Resolving only against the root reported eighteen live
    addresses as dead. So an address resolves if it reaches a file by any of the
    three, and is a defect only when it reaches nothing at all - which is what
    being wrong actually looks like, and what `contracts/requirements.json` is.
    """
    return ((root / ref).exists() or (origin.parent / ref).exists() or ref in suffixes)


def check_reference(root: Path = ROOT) -> list[Defect]:
    """A repository path named in an orientation surface must reach something."""
    suffixes = set()
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            parts = path.relative_to(root).parts
            for start in range(len(parts)):
                suffixes.add("/".join(parts[start:]))
    defects = []
    for path in [root / "CLAUDE.md", *_harness_files(root)]:
        if not path.exists():
            continue
        for ref in sorted(set(PATH_TOKEN.findall(path.read_text(encoding="utf-8")))):
            if ref.startswith(("http", "~")) or ref.startswith(RUNTIME_PREFIXES):
                continue
            if _resolves(ref, path, suffixes, root):
                continue
            defects.append(Defect("REFERENCE", f"{path.relative_to(root)} names {ref}",
                                  "no such path in the tree, from the root or from this file"))
    return defects


def _fixture(tmp: Path, agent_tools: str, prompt: str, orientation: str,
             vendored: str = "") -> Path:
    """A minimal tree carrying exactly the three claim surfaces this grades."""
    root = tmp / "tree"
    (root / ".claude" / "agents").mkdir(parents=True)
    (root / ".claude" / "workflows").mkdir(parents=True)
    (root / "contracts").mkdir(parents=True)
    (root / ".claude" / "agents" / "a.md").write_text(
        f"---\nname: a\ntools: {agent_tools}\n---\n", encoding="utf-8")
    (root / ".claude" / "workflows" / "w.js").write_text(prompt, encoding="utf-8")
    (root / "CLAUDE.md").write_text(orientation, encoding="utf-8")
    (root / "STATUS.yaml").write_text("asset_service_status: BUILT_SELF_TESTED_NOT_WITNESSED\n",
                                      encoding="utf-8")
    if vendored:
        skill = root / ".claude" / "skills" / "v"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(vendored, encoding="utf-8")
    (root / "contracts" / "harness-hosts.json").write_text(
        json.dumps({"portable": ["Bash", "Read"], "retired": {"PowerShell": "not a tool name"}}),
        encoding="utf-8")
    return root


def selfcheck() -> int:
    """Prove each refusal fires, and that a clean tree is not refused.

    A checker that never refuses passes every repository silently. Each case below
    changes exactly one claim away from a supported one and asserts the matching
    kind is reported; the control changes nothing and asserts silence.
    """
    import tempfile

    sourced = ("---\nmetadata:\n  bdos: true\n  author: a\n  origin: o\n"
               "  adopted: 2026-01-01\n  verified: 2026-01-01\n  artifact_digest: sha256:x\n---\n")
    orphan = "---\nmetadata:\n  bdos: true\n---\n"
    clean = ("Bash, Read", "asset_service_status is BUILT_SELF_TESTED_NOT_WITNESSED",
             "see `CLAUDE.md`", sourced)
    cases = [
        ("control", clean, None),
        ("CAPABILITY", ("Bash, PowerShell, Read", clean[1], clean[2], sourced), "CAPABILITY"),
        ("STANDING", (clean[0], "asset_service_status is BUILT_AND_WITNESSED", clean[2], sourced),
         "STANDING"),
        ("REFERENCE", (clean[0], clean[1], "see `contracts/gone.json`", sourced), "REFERENCE"),
        ("PROVENANCE", (clean[0], clean[1], clean[2], orphan), "PROVENANCE"),
    ]
    failures = []
    for name, (tools, prompt, orientation, vendored), expect in cases:
        with tempfile.TemporaryDirectory() as tmp:
            root = _fixture(Path(tmp), tools, prompt, orientation, vendored)
            found = {d.kind for d in
                     check_capability(root) + check_standing(root) + check_reference(root)
                     + check_provenance(root)}
            if expect is None and found:
                failures.append(f"{name}: a supported tree was refused with {sorted(found)}")
            elif expect is not None and expect not in found:
                failures.append(f"{name}: refusal did not fire; reported {sorted(found) or 'nothing'}")
            else:
                print(f"  {name:<11} {'silent' if expect is None else expect + ' fired'}")
    if failures:
        print("\nselfcheck FAILED")
        for line in failures:
            print(f"  {line}")
        return 1
    print(f"harness claim refusals: {len(cases)} cases, every declared refusal fires")
    return 0


#: A vendored core carries its origin repository's frontmatter. These are the fields
#: that make the copy an accountable projection rather than an untracked fork.
PROVENANCE_FIELDS = ("author", "origin", "adopted", "verified", "artifact_digest")


def check_provenance(root: Path = ROOT) -> list[Defect]:
    """A skill vendored from another repository must declare where it came from.

    This checks that the declaration is complete, not that the digest still
    describes the bytes. Recomputing it would mean reimplementing the origin
    repository's own digest rule here, and two implementations of one rule drift
    into disagreeing about what a copy is. Verifying the digest is a
    DEPENDENCY_SEAM: it needs the origin repository's gate, which needs a named
    boundary and a decision record (AGENTS.md, Technical baseline). What this
    refuses is the cheaper and more common failure - a copy landing with no
    declared source at all.
    """
    defects = []
    for path in sorted((root / ".claude" / "skills").glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        if "bdos: true" not in text:
            continue
        missing = [f for f in PROVENANCE_FIELDS if not re.search(rf"^\s*{f}:", text, re.M)]
        if missing:
            defects.append(Defect(
                "PROVENANCE", f"{path.relative_to(root)} is vendored",
                f"declares no {', '.join(missing)}; a copy without a source is a fork"))
    return defects


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "selfcheck":
        return selfcheck()
    defects = (check_capability() + check_standing() + check_reference()
               + check_provenance())
    graded = len(_harness_files()) + 1
    if defects:
        print(f"harness claims: {len(defects)} defect(s) across {graded} graded files\n")
        for defect in defects:
            print(defect)
        print("\nEach line is a claim the harness makes that its owning record does not "
              "support. Repair the claim, or the record if the record is what is wrong.")
        return 1
    print(f"harness claims: {graded} files graded, capability, standing, reference and "
          f"provenance assertions all supported by their owning records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
