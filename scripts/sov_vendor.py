#!/usr/bin/env python3
"""Grade the cores carried from another repository against the decision that carried them.

`decisions/0103-carry-two-bdos-cores.md` records two byte copies from
`bdf1992/bdos@e715cb11` with their sha256 at carry, and names its own defeating
condition: "Either file drifting from the upstream digest above without a
decision saying so." Nothing performed that check. The digest table was written
so a later reader could tell whether the copy still matches, and a table only a
reader consults is a table that goes stale between readers.

The decision is the provenance source. This does not mint a second registry of
copied digests beside it, and it does not reimplement bdos's own
`artifact_digest`, which elides a core's currency block so a re-stamp does not
invalidate it. That rule belongs to bdos; two implementations of one rule drift
into disagreeing about what a copy is. This asks a different question with a
different owner - has the copy in this tree changed since it was carried - and
answers it with a plain digest of the bytes.

Two directions, because one is silence:

  rows -> tree   every digest the decision records still matches its file
  tree -> rows   every skill declaring bdos provenance has a row

Without the second, a third core could arrive carrying no decision at all and
the check would pass by never looking at it.

`sync` is the attended half. Whether bdos has since edited a core cannot be
answered from this repository alone; it needs the upstream tree, and CI does not
have one. It reports rather than refuses, and its silence is not confirmation.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
DECISION = ROOT / "decisions" / "0103-carry-two-bdos-cores.md"

#: One row of the decision's digest table.
ROW = re.compile(r"^\| `(?P<skill>[a-z0-9-]+)` \| `(?P<digest>[0-9a-f]{64})` \|$", re.M)
#: The upstream commit the decision pins, e.g. `bdf1992/bdos@e715cb11`.
PIN = re.compile(r"`(?P<repo>[\w.-]+/[\w.-]+)@(?P<commit>[0-9a-f]{7,40})`")


def carried(decision: Path = DECISION) -> dict[str, str]:
    """Skill name to recorded digest, read from the decision that carried them."""
    return {m.group("skill"): m.group("digest") for m in ROW.finditer(
        decision.read_text(encoding="utf-8"))}


def pin(decision: Path = DECISION) -> tuple[str, str] | None:
    """The upstream repository and commit the decision pins, if it states one."""
    match = PIN.search(decision.read_text(encoding="utf-8"))
    return (match.group("repo"), match.group("commit")) if match else None


def declares_provenance(root: Path = ROOT) -> list[str]:
    """Every skill whose frontmatter claims it came from bdos."""
    return sorted(p.parent.name for p in (root / ".claude" / "skills").glob("*/SKILL.md")
                  if "bdos: true" in p.read_text(encoding="utf-8"))


def check(root: Path = ROOT, decision: Path | None = None) -> list[str]:
    """Both directions between the decision's table and the tree."""
    decision = decision or (root / "decisions" / "0103-carry-two-bdos-cores.md")
    rows = carried(decision)
    defects = []
    if not rows:
        return [f"{decision.name} carries no parseable digest row; the carry has no record"]
    if pin(decision) is None:
        defects.append(f"{decision.name} names no upstream commit; a copy with no pinned "
                       f"source cannot be compared to anything")

    for skill, expected in sorted(rows.items()):
        path = root / ".claude" / "skills" / skill / "SKILL.md"
        if not path.is_file():
            defects.append(f"{skill}: the decision carries it, the tree does not hold it")
            continue
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if observed != expected:
            defects.append(f"{skill}: drifted from the digest at carry\n"
                           f"    recorded {expected}\n    observed {observed}")

    for skill in declares_provenance(root):
        if skill not in rows:
            defects.append(f"{skill}: declares bdos provenance and no decision row carries "
                           f"it; a copy that arrived without a decision")
    return defects


def sync(upstream: Path) -> int:
    """Attended: compare the recorded digests against the upstream tree.

    Answers what this repository cannot ask alone. Reports; never refuses.
    """
    rows, pinned = carried(), pin()
    if pinned is None:
        print("no upstream pin in the decision; nothing to compare against")
        return 1
    repo, commit = pinned
    print(f"decision pins {repo}@{commit}; reading {upstream}")
    if not (upstream / ".git").is_dir():
        print(f"UNREACHABLE: {upstream} is not a git tree. Silence here is not confirmation.")
        return 1

    def show(ref: str, path: str) -> str | None:
        out = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=upstream,
                             capture_output=True)
        return hashlib.sha256(out.stdout).hexdigest() if out.returncode == 0 else None

    head = subprocess.run(["git", "rev-parse", "--short", "origin/main"], cwd=upstream,
                          capture_output=True, text=True).stdout.strip() or "?"
    moved = 0
    for skill, recorded in sorted(rows.items()):
        path = f"cores/{skill}/SKILL.md"
        at_pin, at_head = show(commit, path), show("origin/main", path)
        if at_pin is None:
            print(f"  {skill:<18} UNREACHABLE at {commit}")
        elif at_pin != recorded:
            print(f"  {skill:<18} PIN MISMATCH: the decision's digest is not what {commit} holds")
            moved += 1
        elif at_head != recorded:
            print(f"  {skill:<18} UPSTREAM MOVED: {commit} matches, origin/main ({head}) does not")
            moved += 1
        else:
            print(f"  {skill:<18} IN SYNC at {commit} and origin/main ({head})")
    print(f"\n{len(rows)} carried core(s), {moved} moved upstream. This is an observation, "
          f"not a gate: a moved core is a decision to take, not a build to fail.")
    return 0


DECISION_TEMPLATE = """# 0103 · Carry two bdos cores into the harness

Byte copies of `bdf1992/bdos@{commit}`, `cores/<name>/SKILL.md`.

| Skill | sha256 |
| --- | --- |
{rows}
"""


def _fixture(tmp: Path, *, body: str = "core\n", recorded: str | None = None,
             extra_skill: str | None = None, commit: str = "e715cb11") -> tuple[Path, Path]:
    """A tree with one carried core, and the decision that carries it."""
    import hashlib as _h
    root = tmp / "tree"
    (root / ".claude" / "skills" / "carried").mkdir(parents=True)
    (root / "decisions").mkdir(parents=True)
    (root / ".claude" / "skills" / "carried" / "SKILL.md").write_text(
        f"---\nmetadata:\n  bdos: true\n---\n{body}", encoding="utf-8")
    if extra_skill:
        d = root / ".claude" / "skills" / extra_skill
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("---\nmetadata:\n  bdos: true\n---\n", encoding="utf-8")
    digest = recorded or _h.sha256(
        (root / ".claude" / "skills" / "carried" / "SKILL.md").read_bytes()).hexdigest()
    decision = root / "decisions" / "0103-carry-two-bdos-cores.md"
    decision.write_text(DECISION_TEMPLATE.format(
        commit=commit, rows=f"| `carried` | `{digest}` |"), encoding="utf-8")
    return root, decision


def selfcheck() -> int:
    """Prove each refusal fires, and that a faithful carry is not refused."""
    import tempfile

    cases = [
        ("control", {}, None, "a copy matching its recorded digest is not refused"),
        ("drifted", {"recorded": "0" * 64}, "drifted from the digest at carry",
         "the defeating condition decisions/0103 names for itself"),
        ("unrecorded", {"extra_skill": "arrived"}, "declares bdos provenance and no decision",
         "a core that arrived carrying no decision at all"),
        ("no pin", {"commit": "none"}, "names no upstream commit",
         "a copy with no pinned source cannot be compared to anything"),
    ]
    failures = []
    for name, kwargs, expect, why in cases:
        with tempfile.TemporaryDirectory() as tmp:
            root, decision = _fixture(Path(tmp), **kwargs)
            found = check(root, decision)
            hit = any(expect in d for d in found) if expect else not found
        if not hit:
            failures.append(f"{name}: expected {expect or 'silence'}, got {found or 'nothing'}")
        else:
            print(f"  {name:<12} {'silent' if expect is None else 'refused':<8} {why}")
    if failures:
        print("\nselfcheck FAILED")
        for line in failures:
            print(f"  {line}")
        return 1
    print(f"carried-core refusals: {len(cases)} cases, every declared refusal fires")
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "selfcheck":
        return selfcheck()
    if len(sys.argv) > 2 and sys.argv[1] == "sync":
        return sync(Path(sys.argv[2]).expanduser().resolve())
    if len(sys.argv) > 1 and sys.argv[1] == "sync":
        print("usage: sov_vendor.py sync <path to the bdos working tree>")
        return 1
    defects = check()
    if defects:
        print(f"carried cores: {len(defects)} defect(s)\n")
        for line in defects:
            print(f"  {line}")
        print(f"\nThe decision that carried these is the record: {DECISION.name}. A copy that "
              f"drifts without a decision saying so defeats its own carry ruling.")
        return 1
    rows = carried()
    print(f"carried cores: {len(rows)} core(s) match the digests "
          f"decisions/0103-carry-two-bdos-cores.md recorded at carry, and every skill "
          f"declaring bdos provenance is carried by a row")
    return 0


if __name__ == "__main__":
    sys.exit(main())
