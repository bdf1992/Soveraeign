"""Cases that prove every declared refusal fires, and that a clean tree does not.

Most of these are regressions for defects that actually shipped in this
repository, not invented shapes; `selfcheck` counts them from the cases rather
than stating a number here, because a hand-written population count beside the
thing that computes it is the defect this module exists to grade. The first
version of the grader passed every one of them: it recognised only
`<subject>_status is <TOKEN>`, so the prose forms it was written in response to
went straight through. A checker is only worth its green run if the cases behind
it are the ones that got past a reader.

The collision case is the sharper one. An earlier REFERENCE rule accepted an
address if any file anywhere in the tree ended with it, so an untracked cache or
an archived copy validated an address that resolved nowhere a reader would look.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from sovharness import contract
import json
import os
import shutil
import subprocess
import tempfile

REAL_ROOT = Path(__file__).resolve().parent.parent.parent

CLEAN_DESCRIPTION = "description: Bounded work in the asset domain.\n"
CLEAN_PROMPT = ("'asset_service_status is BUILT_SELF_TESTED_NOT_WITNESSED'\n"
                "the PUBLIC-CLEARANCE hold blocks public release only\n")
CLEAN_ORIENTATION = "see `contracts/harness-claims.json`\n"
SOURCED = ("---\nmetadata:\n  bdos: true\n  author: a\n  origin: o\n  adopted: 2026-01-01\n"
           "  verified: 2026-01-01\n  artifact_digest: sha256:x\n---\n")


def build(tmp: Path, *, tools: str = "Bash, Read", prompt: str = CLEAN_PROMPT,
          orientation: str = CLEAN_ORIENTATION, description: str = CLEAN_DESCRIPTION,
          vendored: str = SOURCED, plant: str = "", untracked: str = "",
          contract_patch=None) -> Path:
    """A minimal tree carrying exactly the surfaces the grader reads.

    The two contracts are copied from the repository, so a case is graded against
    the vocabulary actually declared rather than a convenient copy of it.
    """
    root = tmp / "tree"
    for sub in (".claude/agents", ".claude/workflows", ".claude/skills/v",
                ".claude/skills/s", "contracts"):
        (root / sub).mkdir(parents=True)
    (root / ".claude" / "agents" / "a.md").write_text(
        f"---\nname: a\n{description}tools: {tools}\n---\n", encoding="utf-8")
    (root / ".claude" / "skills" / "s" / "SKILL.md").write_text(
        f"---\nname: s\n{description}---\n{prompt}", encoding="utf-8")
    (root / ".claude" / "skills" / "v" / "SKILL.md").write_text(vendored, encoding="utf-8")
    (root / ".claude" / "workflows" / "w.js").write_text(prompt, encoding="utf-8")
    (root / "CLAUDE.md").write_text(orientation, encoding="utf-8")
    (root / "STATUS.yaml").write_text(
        "asset_service_status: BUILT_SELF_TESTED_NOT_WITNESSED\n", encoding="utf-8")
    for name in ("harness-hosts.json", "harness-claims.json"):
        shutil.copyfile(REAL_ROOT / "contracts" / name, root / "contracts" / name)
    if plant:
        planted = root / plant
        planted.parent.mkdir(parents=True, exist_ok=True)
        planted.write_text("{}", encoding="utf-8")
    _commit(root)
    if untracked:
        loose = root / untracked
        loose.parent.mkdir(parents=True, exist_ok=True)
        loose.write_text("{}", encoding="utf-8")
    # The copied contract states the real repository's drift footprint, which this
    # tree does not have. Re-derive it here so the control is self-consistent and a
    # patched case is failing on the patch rather than on the fixture's own shape.
    _rebase_footprint(root)
    if contract_patch is not None:
        target = root / "contracts" / "harness-claims.json"
        claims = json.loads(target.read_text(encoding="utf-8"))
        contract_patch(claims)
        target.write_text(json.dumps(claims, indent=2), encoding="utf-8")
    return root


def _commit(root: Path) -> None:
    """A real index, because REFERENCE and the footprint both read git, not the disk."""
    env = {"GIT_AUTHOR_NAME": "f", "GIT_AUTHOR_EMAIL": "f@f", "GIT_COMMITTER_NAME": "f",
           "GIT_COMMITTER_EMAIL": "f@f", "PATH": os.environ.get("PATH", "")}
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "fixture"]):
        subprocess.run(["git", *args], cwd=root, env=env, capture_output=True, check=False)


def _rebase_footprint(root: Path) -> None:
    """Point the copied contract's footprint at this tree instead of the real one."""
    target = root / "contracts" / "harness-claims.json"
    claims = json.loads(target.read_text(encoding="utf-8"))
    for entry in claims.get("known_drift", []):
        files, occurrences = contract._footprint(root, entry["term"])
        entry["footprint"] = {**entry.get("footprint", {}), "files": len(files),
                              "occurrences": occurrences, "paths": files}
    target.write_text(json.dumps(claims, indent=2), encoding="utf-8")


def _drop_a_kind(claims: dict) -> None:
    """A kind the module runs but the contract does not describe."""
    claims["coverage"]["derived"].pop("REFERENCE", None)


def _add_a_kind(claims: dict) -> None:
    """A kind the contract describes but the module never runs."""
    claims["coverage"]["derived"]["IMAGINARY"] = "a kind nothing emits"


def _wrong_paths(claims: dict) -> None:
    """Right counts, wrong paths - what a count-only check would miss."""
    footprint = claims["known_drift"][0]["footprint"]
    footprint["paths"] = [f"made/up/{i}.md" for i in range(footprint["files"])]


def _drop_footprint(claims: dict) -> None:
    """Unenforced drift a reader is given no way to size."""
    claims["known_drift"][0].pop("footprint", None)


def _wrong_footprint(claims: dict) -> None:
    """A hand-written population count that the tree contradicts."""
    claims["known_drift"][0]["footprint"]["files"] += 8


#: (name, kwargs, expected kind or None, why, shipped). `shipped` says whether this
#: case reproduces a defect that actually reached this repository - a historical
#: fact, declared on the case itself because there is nothing to derive it from.
#: It was a separate tuple of names beside the cases, which is the shape that
#: drifts: nothing tied a name in that list to a case, and the comment claimed the
#: count came from reading `why`, which no code did.
CASES = (
    ("control", {}, None, "a supported tree is not refused", False),
    ("CAPABILITY", {"tools": "Bash, Telepathy, Read"}, "CAPABILITY",
     "a tool no declared environment provides is a capability no invocation can grant",
     False),
    ("STANDING", {"prompt": "'asset_service_status is BUILT_AND_WITNESSED'\n"}, "STANDING",
     "sov-console.js asserted a token STATUS.yaml contradicts", True),
    ("REFERENCE", {"orientation": "see `contracts/gone.json`\n"}, "REFERENCE",
     "CLAUDE.md named contracts/requirements.json, which does not exist", True),
    ("REFERENCE/unlisted", {"orientation": "see `contracts/quarterly-plan.yaml`\n"},
     "REFERENCE", "an address nobody anticipated is refused without being listed", False),
    ("CAPABILITY/unlisted", {"tools": "Bash, Kubernetes, Read"}, "CAPABILITY",
     "a tool no declared environment provides is refused without being listed", False),
    ("CAPABILITY/non-portable", {"tools": "Bash, PowerShell, Read"}, None,
     "a tool only the workstation provides is admissible; grading portability instead "
     "deleted PowerShell from four definitions on the evidence of one container", True),
    ("STANDING/unlisted", {"prompt": "'banana_service_status is BUILT'\n"}, "STANDING",
     "a subject STATUS.yaml never had is refused without being listed", False),
    ("STANDING/colon", {"prompt": "`asset_service_status: WITNESSED` per STATUS.yaml\n"},
     "STANDING",
     "three skills quoted a false standing in the colon spelling the old form missed", True),
    ("REFERENCE/tracked-copy", {"orientation": "see `contracts/gone.json`\n",
                                "plant": "archives/old/contracts/gone.json"}, "REFERENCE",
     "a tracked archived copy at a colliding suffix must not validate an address", False),
    ("REFERENCE/untracked", {"orientation": "see `contracts/gone.json`\n",
                             "untracked": "contracts/gone.json"}, "REFERENCE",
     "an untracked file at the exact named path must not validate it either", False),
    ("PROVENANCE", {"vendored": "---\nmetadata:\n  bdos: true\n---\n"}, "PROVENANCE",
     "a vendored copy with no declared source is a fork", True),
    ("SELFCLAIM/kind-missing", {"contract_patch": _drop_a_kind}, "SELFCLAIM",
     "the contract described a smaller kind set than the module ran", True),
    ("SELFCLAIM/kind-extra", {"contract_patch": _add_a_kind}, "SELFCLAIM",
     "a described kind the module does not run reads to a participant as coverage", True),
    ("SELFCLAIM/footprint", {"contract_patch": _wrong_footprint}, "SELFCLAIM",
     "the contract stated a drift footprint the tree contradicts", True),
    ("SELFCLAIM/paths", {"contract_patch": _wrong_paths}, "SELFCLAIM",
     "counts that match while the listed paths do not are still a wrong footprint", False),
    ("SELFCLAIM/no-footprint", {"contract_patch": _drop_footprint}, "SELFCLAIM",
     "unenforced drift with no footprint cannot be sized by a reader", False),
)



def selfcheck(grade: Callable[[Path], list], declared_kinds: set | None = None) -> int:
    """Run every case. A checker that cannot refuse passes every repository."""
    declared_kinds = set(declared_kinds or ())
    failures = []
    for name, kwargs, expect, why, _shipped in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            found = {d.kind for d in grade(build(Path(tmp), **kwargs))}
        if expect is None and found:
            failures.append(f"{name}: a supported tree was refused with {sorted(found)}")
        elif expect is not None and expect not in found:
            failures.append(f"{name}: refusal did not fire; reported {sorted(found) or 'nothing'}")
        else:
            print(f"  {name:<20} {'silent' if expect is None else expect + ' fired':<18} {why}")
    exercised = {expect for _, _, expect, _, _ in CASES if expect}
    unexercised = declared_kinds - exercised
    if unexercised:
        failures.append(
            f"{sorted(unexercised)} declared by a check but produced by no case; a kind "
            f"whose Defect literal is renamed away from its @emits name would go unseen")

    if failures:
        print("\nselfcheck FAILED")
        for line in failures:
            print(f"  {line}")
        return 1
    regressions = sum(1 for case in CASES if case[4])
    print(f"harness claim refusals: {len(CASES)} cases, every declared refusal fires; "
          f"{regressions} are regressions for defects this repository actually shipped")
    return 0
