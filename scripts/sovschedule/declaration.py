"""Load and check scheduled-run declarations under ``.claude/schedules/``.

A declaration is the harness analogue of an operation plan: it names the
target, the cadence, the mode, the effect class, the preconditions, and the
limits before anything runs. Loading refuses what this unattended harness is not admitted to fire:
an EXTERNAL_WORLD effect class, a target that does not exist, an unparseable
cron expression, or a build-mode run on a shared dirty tree. That local ceiling
does not imply other operations are globally phase-refused.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from sovschedule import cron, jsonshape


SCHEDULES_DIR = Path(".claude") / "schedules"
SCHEMA_NAME = "schedule.schema.json"
EXTERNAL_WORLD = "EXTERNAL_WORLD"


class DeclarationError(ValueError):
    """A declaration is malformed or names something the harness refuses."""


@dataclass(frozen=True)
class Declaration:
    """One checked schedule declaration."""

    name: str
    path: Path
    description: str
    enabled: bool
    target_kind: str
    target_name: str
    target_args: dict
    spec: cron.CronSpec
    mode: str
    effect_class: str
    isolation: str
    clean_tree: bool
    lookback_minutes: int
    max_budget_usd: float
    timeout_seconds: int


def load_schema(root: Path) -> dict:
    """Read the declaration schema from the repository."""
    return json.loads((root / SCHEDULES_DIR / SCHEMA_NAME).read_text(encoding="utf-8"))


def target_path(root: Path, kind: str, name: str) -> Path:
    """Repository file that must exist for a target to be schedulable."""
    if kind == "workflow":
        return root / ".claude" / "workflows" / f"{name}.js"
    return root / ".claude" / "skills" / name / "SKILL.md"


def _semantic_defects(root: Path, path: Path, raw: dict,
                      require_target: bool = True) -> list[str]:
    defects = []
    if raw["name"] != path.stem:
        defects.append(f"name '{raw['name']}' must equal the file stem '{path.stem}'")
    if raw["effect_class"] == EXTERNAL_WORLD:
        defects.append("EXTERNAL_WORLD refused: unattended scheduler has no admitted external crossing")
    target = raw["target"]
    if require_target and not target_path(root, target["kind"], target["name"]).is_file():
        defects.append(f"{target['kind']} '{target['name']}' not found under .claude/")
    try:
        cron.parse(raw["cron"])
    except ValueError as error:
        defects.append(str(error))
    preconditions = raw.get("preconditions", {})
    isolation = raw.get("isolation", "tree")
    if raw["mode"] == "build" and isolation == "tree" and not preconditions.get("clean_tree", True):
        defects.append(
            "build mode on the shared tree requires preconditions.clean_tree true "
            "or isolation worktree"
        )
    return defects


def load_declaration(root: Path, path: Path,
                     require_target: bool = True) -> Declaration:
    """Load one declaration; raise DeclarationError listing every defect found.

    ``require_target`` is True for every reader that intends to run the thing, which is
    all of them but one. The switch operation passes False, because a schedule whose
    workflow file was deleted is exactly the schedule an operator needs to switch off,
    and refusing to load it traps it on. That operation does its own target check, and
    only in the arming direction.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DeclarationError(f"{path.name}: {error}") from None
    defects = jsonshape.check(raw, load_schema(root))
    if not defects:
        defects = _semantic_defects(root, path, raw, require_target=require_target)
    if defects:
        raise DeclarationError(f"{path.name}: " + "; ".join(defects))
    preconditions = raw.get("preconditions", {})
    limits = raw["limits"]
    return Declaration(
        name=raw["name"],
        path=path,
        description=raw.get("description", ""),
        enabled=raw["enabled"],
        target_kind=raw["target"]["kind"],
        target_name=raw["target"]["name"],
        target_args=raw["target"].get("args", {}),
        spec=cron.parse(raw["cron"]),
        mode=raw["mode"],
        effect_class=raw["effect_class"],
        isolation=raw.get("isolation", "tree"),
        clean_tree=preconditions.get("clean_tree", raw["mode"] == "build"),
        lookback_minutes=preconditions.get("lookback_minutes", 60),
        max_budget_usd=float(limits["max_budget_usd"]),
        timeout_seconds=int(limits["timeout_seconds"]),
    )


def load_all(root: Path) -> list[Declaration]:
    """Load every declaration in the schedules directory, sorted by file name."""
    directory = root / SCHEDULES_DIR
    paths = sorted(p for p in directory.glob("*.json") if p.name != SCHEMA_NAME)
    return [load_declaration(root, path) for path in paths]
