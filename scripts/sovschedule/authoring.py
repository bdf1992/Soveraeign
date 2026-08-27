"""Create a schedule declaration, and edit one. The other two changes a schedule has.

``control.set_switch`` moves the enabled flag. This writes everything else: a new
declaration, or a change to the nine fields that decide what a schedule runs, when, and
at what cost. The authority rule falls out of the one already there rather than being a
second story - changing a schedule that is armed is the owner's, because that is a
change to what runs unattended, and creating one already armed is arming one.

Nothing here invents a field. A declaration validates against
``.claude/schedules/schedule.schema.json`` and then against the same semantic checks the
runner applies, so a form cannot write a document the runner would later refuse. The
refusal an operator sees is the loader's own wording, because two descriptions of the
same defect drift.

Nothing here commits, and nothing here deletes. Removing a declaration is not offered:
an uncommitted one has no copy anywhere and the operator who typed it would be the only
thing that ever knew. Switching it off is the reversible answer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import re

from sovschedule import changelog, control
from sovschedule.declaration import (
    SCHEDULES_DIR, EXTERNAL_WORLD, DeclarationError, load_declaration,
)

#: The fields a declaration carries, in the order they are written. ``name`` is here and
#: is not editable: it must equal the file stem, so changing it is creating a different
#: schedule and deleting one, which this module does not do.
FIELDS = ("name", "description", "enabled", "target", "cron", "mode", "effect_class",
          "isolation", "preconditions", "limits")

EDITABLE = tuple(field for field in FIELDS if field not in ("name", "enabled"))

#: A schedule name is a file stem, so it has to be one. Rejected early and by shape
#: rather than by letting a path separator reach the filesystem.
NAME_SHAPE = re.compile(r"^[a-z][a-z0-9-]{1,48}[a-z0-9]$")

REFUSALS = ("NAME_SHAPE", "ALREADY_EXISTS", "UNKNOWN_SCHEDULE", "REASON_MISSING",
            "GRANT_NOT_HELD", "INVALID_DECLARATION", "NOT_EDITABLE",
            "EXTERNAL_WORLD_REFUSED")


def _refuse(root: Path, *, name: str, change: str, actor: control.Actor, reason: str,
            code: str, detail: str, now: datetime) -> control.Outcome:
    entry = changelog.record(
        schedule=name, change=change, direction="", from_enabled=None, to_enabled=None,
        actor_id=actor.actor_id, actor_kind=actor.actor_kind, binding=actor.binding,
        reason=reason, occurred_at=now, outcome=changelog.REFUSED, refusal_code=code)
    changelog.append(root, entry)
    return control.Outcome(changelog.REFUSED, name, "", code, detail, entry)


def _validates(root: Path, path: Path, body: dict) -> str | None:
    """Write, load, and report the loader's own complaint. Returns None when clean.

    The document is written before it is checked because the loader reads a file and
    checks the name against its stem, and reimplementing either here would create a
    second opinion about what a valid declaration is. The caller restores the previous
    bytes when this returns a complaint.
    """
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")
    try:
        load_declaration(root, path)
    except DeclarationError as error:
        return str(error)
    return None


def _authority(actor: control.Actor, armed: bool) -> str | None:
    """The grant this change needs, or None. Armed is what makes a change the owner's."""
    if not armed:
        return None
    return None if actor.holds_grant("seat:root") else "seat:root"


def create(root: Path, name: str, body: dict, actor: control.Actor, reason: str,
           now: datetime | None = None) -> control.Outcome:
    """Write a declaration that did not exist. Armed on creation needs the owner."""
    now = now or datetime.now(timezone.utc)
    if not reason.strip():
        return _refuse(root, name=name, change=changelog.CREATE, actor=actor,
                       reason=reason, code="REASON_MISSING", now=now,
                       detail="a declaration with no reason for existing is one nobody "
                              "can decide to remove later")
    if not NAME_SHAPE.match(name or ""):
        return _refuse(root, name=name or "", change=changelog.CREATE, actor=actor,
                       reason=reason, code="NAME_SHAPE", now=now,
                       detail=f"{name!r} is not a usable file stem: lower case, digits "
                              "and hyphens, 3 to 50 characters, starting with a letter")
    path = root / SCHEDULES_DIR / f"{name}.json"
    if path.exists():
        return _refuse(root, name=name, change=changelog.CREATE, actor=actor,
                       reason=reason, code="ALREADY_EXISTS", now=now,
                       detail=f"{name} already exists; edit it rather than replacing it")

    body = dict(body)
    body["name"] = name
    body.setdefault("enabled", False)
    if body.get("effect_class") == EXTERNAL_WORLD:
        return _refuse(root, name=name, change=changelog.CREATE, actor=actor,
                       reason=reason, code="EXTERNAL_WORLD_REFUSED", now=now,
                       detail="EXTERNAL_WORLD is refused in this phase; the loader "
                              "refuses it too and this says so before writing a file")
    needed = _authority(actor, bool(body["enabled"]))
    if needed:
        return _refuse(root, name=name, change=changelog.CREATE, actor=actor,
                       reason=reason, code="GRANT_NOT_HELD", now=now,
                       detail=f"creating a schedule already armed is arming one, which "
                              f"needs {needed}. Create it switched off and arm it "
                              "separately, which is a decision with its own record")

    complaint = _validates(root, path, _ordered(body))
    if complaint:
        path.unlink(missing_ok=True)
        return _refuse(root, name=name, change=changelog.CREATE, actor=actor,
                       reason=reason, code="INVALID_DECLARATION", now=now,
                       detail=complaint)

    entry = changelog.record(
        schedule=name, change=changelog.CREATE, direction="", fields=tuple(body),
        from_enabled=None, to_enabled=bool(body["enabled"]), actor_id=actor.actor_id,
        actor_kind=actor.actor_kind, binding=actor.binding, reason=reason,
        occurred_at=now, outcome=changelog.EFFECTED,
        after_digest=changelog.digest_text(path.read_text(encoding="utf-8")))
    changelog.append(root, entry)
    return control.Outcome(
        changelog.EFFECTED, name, "", None,
        f"{name} created, switched off, and not committed. Arm it when you want it to "
        "run - that is a separate decision and gets its own record.", entry)


def update(root: Path, name: str, changes: dict, actor: control.Actor, reason: str,
           now: datetime | None = None) -> control.Outcome:
    """Edit an existing declaration. Editing an armed one is the owner's."""
    now = now or datetime.now(timezone.utc)
    if not reason.strip():
        return _refuse(root, name=name, change=changelog.UPDATE, actor=actor,
                       reason=reason, code="REASON_MISSING", now=now,
                       detail="an edit with no reason cannot be reviewed later")
    path = root / SCHEDULES_DIR / f"{name}.json"
    if not path.is_file():
        return _refuse(root, name=name, change=changelog.UPDATE, actor=actor,
                       reason=reason, code="UNKNOWN_SCHEDULE", now=now,
                       detail=f"no declaration named {name}")

    stray = [field for field in changes if field not in EDITABLE]
    if stray:
        return _refuse(root, name=name, change=changelog.UPDATE, actor=actor,
                       reason=reason, code="NOT_EDITABLE", now=now,
                       detail=f"{stray} cannot be edited here. name is the file stem, so "
                              "changing it creates a different schedule and removes this "
                              "one; enabled is the switch and has its own operation, "
                              "because arming is a different decision from editing")

    before_bytes = path.read_bytes()
    before = before_bytes.decode("utf-8")
    try:
        body = json.loads(before)
    except json.JSONDecodeError as error:
        return _refuse(root, name=name, change=changelog.UPDATE, actor=actor,
                       reason=reason, code="INVALID_DECLARATION", now=now,
                       detail=f"{name}.json does not parse ({error}); repair it first")

    needed = _authority(actor, bool(body.get("enabled")))
    if needed:
        return _refuse(root, name=name, change=changelog.UPDATE, actor=actor,
                       reason=reason, code="GRANT_NOT_HELD", now=now,
                       detail=f"{name} is armed, so editing it changes what runs "
                              f"unattended. That needs {needed}. Switch it off first, "
                              "which anyone may do, then edit it")

    moved = tuple(field for field in changes if body.get(field) != changes[field])
    if not moved:
        return control.Outcome(changelog.UNCHANGED, name, "", None,
                               f"{name} already holds those values. Nothing written.", {})
    body.update(changes)
    if body.get("effect_class") == EXTERNAL_WORLD:
        return _refuse(root, name=name, change=changelog.UPDATE, actor=actor,
                       reason=reason, code="EXTERNAL_WORLD_REFUSED", now=now,
                       detail="EXTERNAL_WORLD is refused in this phase")

    complaint = _validates(root, path, _ordered(body))
    if complaint:
        # The exact bytes, not an equivalent document. Rewriting through write_text
        # normalises line endings, so a rollback on this host would silently convert a
        # CRLF file to LF and report that it had changed nothing.
        path.write_bytes(before_bytes)
        return _refuse(root, name=name, change=changelog.UPDATE, actor=actor,
                       reason=reason, code="INVALID_DECLARATION", now=now,
                       detail=complaint)

    entry = changelog.record(
        schedule=name, change=changelog.UPDATE, direction="", fields=moved,
        from_enabled=bool(body.get("enabled")), to_enabled=bool(body.get("enabled")),
        actor_id=actor.actor_id, actor_kind=actor.actor_kind, binding=actor.binding,
        reason=reason, occurred_at=now, outcome=changelog.EFFECTED,
        before_digest=changelog.digest_text(before),
        after_digest=changelog.digest_text(path.read_text(encoding="utf-8")))
    changelog.append(root, entry)
    return control.Outcome(
        changelog.EFFECTED, name, "", None,
        f"{name} updated: {', '.join(moved)}. Changed in the working tree and not "
        "committed.", entry)


def _ordered(body: dict) -> dict:
    """Declared fields in the declared order, then anything else, so diffs stay readable."""
    out = {field: body[field] for field in FIELDS if field in body}
    out.update({key: value for key, value in body.items() if key not in out})
    return out


def blank(name: str = "") -> dict:
    """A declaration with every field present and nothing decided that matters.

    Switched off, observe-only, and pointed at nothing, so a form starts from a document
    that is honest about being incomplete rather than from one that would run.
    """
    return {
        "name": name,
        "description": "",
        "enabled": False,
        "target": {"kind": "workflow", "name": "", "args": {}},
        "cron": "0 3 * * *",
        "mode": "observe",
        "effect_class": "RESOURCE_CONSUMPTION",
        "isolation": "tree",
        "preconditions": {"clean_tree": False, "lookback_minutes": 60},
        "limits": {"max_budget_usd": 3, "timeout_seconds": 1800},
    }


def targets(root: Path) -> list[dict]:
    """Every workflow and skill a schedule could point at, sorted, kind first.

    Read off the filesystem rather than from a registry, because the loader's target
    check reads the filesystem too and a list that disagreed with it would offer an
    operator a choice the save then refuses.
    """
    found = []
    for path in sorted((root / ".claude" / "workflows").glob("*.js")):
        found.append({"kind": "workflow", "name": path.stem})
    skills = root / ".claude" / "skills"
    if skills.is_dir():
        for path in sorted(skills.iterdir()):
            if (path / "SKILL.md").is_file():
                found.append({"kind": "skill", "name": path.name})
    return found
