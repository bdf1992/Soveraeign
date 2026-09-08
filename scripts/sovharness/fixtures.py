"""Cases that prove every declared refusal fires, and that a clean tree does not.

Four of these are regressions for defects that actually shipped in this
repository, not invented shapes. The first version of the grader passed all of
them: it recognised only `<subject>_status is <TOKEN>`, so the prose forms it was
written in response to went straight through. A checker is only worth its green
run if the cases behind it are the ones that got past a reader.

The collision case is the sharper one. An earlier REFERENCE rule accepted an
address if any file anywhere in the tree ended with it, so an untracked cache or
an archived copy validated an address that resolved nowhere a reader would look.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import json
import shutil
import tempfile

REAL_ROOT = Path(__file__).resolve().parent.parent.parent

CLEAN_DESCRIPTION = "description: Bounded work in the asset domain.\n"
CLEAN_PROMPT = "'asset_service_status is BUILT_SELF_TESTED_NOT_WITNESSED'\n"
CLEAN_ORIENTATION = "see `contracts/harness-claims.json`\n"
SOURCED = ("---\nmetadata:\n  bdos: true\n  author: a\n  origin: o\n  adopted: 2026-01-01\n"
           "  verified: 2026-01-01\n  artifact_digest: sha256:x\n---\n")


def build(tmp: Path, *, tools: str = "Bash, Read", prompt: str = CLEAN_PROMPT,
          orientation: str = CLEAN_ORIENTATION, description: str = CLEAN_DESCRIPTION,
          vendored: str = SOURCED, plant: str = "") -> Path:
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
    return root


#: (name, kwargs, expected kind or None for silence, why this case exists)
CASES = (
    ("control", {}, None, "a supported tree is not refused"),
    ("CAPABILITY", {"tools": "Bash, PowerShell, Read"}, "CAPABILITY",
     "four agent definitions declared PowerShell"),
    ("STANDING", {"prompt": "'asset_service_status is BUILT_AND_WITNESSED'\n"}, "STANDING",
     "sov-console.js asserted a token STATUS.yaml contradicts"),
    ("REFERENCE", {"orientation": "see `contracts/gone.json`\n"}, "REFERENCE",
     "CLAUDE.md named contracts/requirements.json, which does not exist"),
    ("REFERENCE/collision", {"orientation": "see `contracts/gone.json`\n",
                             "plant": "archives/old/contracts/gone.json"}, "REFERENCE",
     "an archived or untracked file must not validate an address"),
    ("VOLATILE/unbuilt",
     {"description": "description: Charter work while the service is accepted but unbuilt.\n"},
     "VOLATILE", "sov-console and sov-proofing both said this while Console was built"),
    ("VOLATILE/phase",
     {"description": "description: Refuse publication while Phase-I boundaries stand.\n"},
     "VOLATILE", "sdlc-release conditioned a live refusal on a terminal phase"),
    ("RETIRED",
     {"prompt": "Name no_external_effects_in_phase_i in the refusal.\n"}, "RETIRED",
     "sdlc-release told participants to cite a record that no longer exists"),
    ("PROVENANCE", {"vendored": "---\nmetadata:\n  bdos: true\n---\n"}, "PROVENANCE",
     "a vendored copy with no declared source is a fork"),
)


def selfcheck(grade: Callable[[Path], list]) -> int:
    """Run every case. A checker that cannot refuse passes every repository."""
    failures = []
    for name, kwargs, expect, why in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            found = {d.kind for d in grade(build(Path(tmp), **kwargs))}
        if expect is None and found:
            failures.append(f"{name}: a supported tree was refused with {sorted(found)}")
        elif expect is not None and expect not in found:
            failures.append(f"{name}: refusal did not fire; reported {sorted(found) or 'nothing'}")
        else:
            print(f"  {name:<20} {'silent' if expect is None else expect + ' fired':<18} {why}")
    if failures:
        print("\nselfcheck FAILED")
        for line in failures:
            print(f"  {line}")
        return 1
    print(f"harness claim refusals: {len(CASES)} cases, every declared refusal fires; "
          f"four are regressions for defects this repository actually shipped")
    return 0
