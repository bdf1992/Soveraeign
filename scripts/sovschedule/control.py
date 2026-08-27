"""The one operation that moves a schedule's switch. Both bindings call this.

``contracts/automation-control.json`` is the declaration; this is the implementation.
The page's button and the command line reach this function and nothing else, so the
authority check lives here rather than in either binding. A control merely hidden from
a page is not an authority check: the command line reaches the same operation, and so
does anything that imports this module.

The two directions are not symmetric. Arming a schedule commits resources that will be
spent without anyone watching, so it needs the owner's grant. Stopping one consumes
nothing and reverses in a keystroke, so it needs nobody's. A surface that asks
permission before letting an operator switch something off is unusable during the exact
incident it exists for.

Nothing here commits. The changed declaration is left in the working tree for whoever
holds the branch.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import re

from sovschedule import changelog
from sovschedule.declaration import (
    SCHEDULES_DIR, DeclarationError, load_declaration, target_path,
)

#: Who is asking, and through what. The binding is recorded because a page click and a
#: command line are different evidence about what happened, even from the same person.
BINDING_CONSOLE = "console"
BINDING_COMMAND = "command"

#: Actor kinds, matching CLASSIFICATION.md. The console cannot tell operators apart, so
#: it records what it actually knows: a local human at this box.
HUMAN = "HUMAN"
MODEL = "MODEL"

#: Which grant each direction needs. Empty means the direction needs none.
GRANT_FOR = {changelog.ENABLE: "seat:root", changelog.DISABLE: ""}

REFUSALS = ("UNKNOWN_SCHEDULE", "NOT_A_DIRECTION", "GRANT_NOT_HELD", "REASON_MISSING",
            "DECLARATION_REFUSED", "TARGET_MISSING")


@dataclass(frozen=True)
class Actor:
    """Who is asking. ``holds`` is the set of seats this actor may act as."""

    actor_id: str
    actor_kind: str
    binding: str
    holds: frozenset[str] = frozenset()

    def holds_grant(self, grant: str) -> bool:
        return not grant or grant in self.holds


@dataclass(frozen=True)
class Outcome:
    """What the operation did. ``entry`` is the line appended to the switch log."""

    outcome: str
    schedule: str
    direction: str
    refusal_code: str | None
    detail: str
    entry: dict

    @property
    def moved(self) -> bool:
        return self.outcome == changelog.EFFECTED

    @property
    def exit_code(self) -> int:
        """A refusal is a nonzero exit; a recorded proposal is not a failure."""
        return 1 if self.outcome == changelog.REFUSED else 0


def owner(binding: str = BINDING_CONSOLE) -> Actor:
    """The local operator at this box, who is the only one that can arm anything.

    The console cannot authenticate. It records that the actor was local and holds the
    root seat by possession of the machine, and it does not claim an identity it never
    checked - which is why ``actor_id`` says local-operator rather than naming a person.
    """
    return Actor(actor_id="urn:soveraeign:actor:local-operator", actor_kind=HUMAN,
                 binding=binding, holds=frozenset({"seat:root"}))


def model(actor_id: str, binding: str = BINDING_COMMAND) -> Actor:
    """A model operator. It may switch a schedule off and may only propose switching one on."""
    return Actor(actor_id=actor_id, actor_kind=MODEL, binding=binding, holds=frozenset())


def declaration_path(root: Path, name: str) -> Path:
    return root / SCHEDULES_DIR / f"{name}.json"


def _refuse(root: Path, *, schedule: str, direction: str, actor: Actor, reason: str,
            code: str, detail: str, now: datetime, from_enabled: bool | None) -> Outcome:
    entry = changelog.record(
        schedule=schedule, change=changelog.SWITCH, direction=direction,
        from_enabled=from_enabled,
        to_enabled=from_enabled, actor_id=actor.actor_id, actor_kind=actor.actor_kind,
        binding=actor.binding, reason=reason, occurred_at=now,
        outcome=changelog.REFUSED, refusal_code=code)
    changelog.append(root, entry)
    return Outcome(changelog.REFUSED, schedule, direction, code, detail, entry)


def set_switch(root: Path, name: str, direction: str, actor: Actor, reason: str,
               now: datetime | None = None) -> Outcome:
    """Move one schedule's switch, or record why it did not move.

    Every path through here appends exactly one line to the switch log, including the
    refusals, except the no-op: setting a switch to the state it already holds writes
    nothing at all, because two operators clicking the same button is one transition.
    """
    now = now or datetime.now(timezone.utc)
    if direction not in GRANT_FOR:
        return _refuse(root, schedule=name, direction=direction, actor=actor,
                       reason=reason, code="NOT_A_DIRECTION", from_enabled=None, now=now,
                       detail=f"{direction!r} is neither ENABLE nor DISABLE")
    if not reason.strip():
        return _refuse(root, schedule=name, direction=direction, actor=actor,
                       reason=reason, code="REASON_MISSING", from_enabled=None, now=now,
                       detail="a switch record with no reason answers who and when and "
                              "not the only question anyone asks afterwards")

    path = declaration_path(root, name)
    if not path.is_file():
        return _refuse(root, schedule=name, direction=direction, actor=actor,
                       reason=reason, code="UNKNOWN_SCHEDULE", from_enabled=None, now=now,
                       detail=f"no declaration named {name} under {SCHEDULES_DIR.as_posix()}")
    try:
        # Not require_target: a schedule whose workflow was deleted must still be
        # switchable off, and the arming direction checks the target itself below.
        declared = load_declaration(root, path, require_target=False)
    except DeclarationError as error:
        return _refuse(root, schedule=name, direction=direction, actor=actor,
                       reason=reason, code="DECLARATION_REFUSED", from_enabled=None,
                       now=now, detail=f"{error}; repair it before switching it")

    wanted = direction == changelog.ENABLE
    if declared.enabled == wanted:
        return Outcome(changelog.UNCHANGED, name, direction, None,
                       f"{name} is already {_word(wanted)}. Nothing was written and "
                       "nothing was recorded, because nothing moved.", {})

    if wanted and not target_path(root, declared.target_kind, declared.target_name).is_file():
        return _refuse(root, schedule=name, direction=direction, actor=actor,
                       reason=reason, code="TARGET_MISSING", from_enabled=declared.enabled,
                       now=now, detail=f"{declared.target_kind} {declared.target_name} does "
                                       "not exist, so arming this would arm a run that "
                                       "cannot execute")

    grant = GRANT_FOR[direction]
    if not actor.holds_grant(grant):
        entry = changelog.record(
            schedule=name, change=changelog.SWITCH, direction=direction,
            from_enabled=declared.enabled,
            to_enabled=declared.enabled, actor_id=actor.actor_id,
            actor_kind=actor.actor_kind, binding=actor.binding, reason=reason,
            occurred_at=now, outcome=changelog.PROPOSED, refusal_code="GRANT_NOT_HELD")
        changelog.append(root, entry)
        return Outcome(changelog.PROPOSED, name, direction, "GRANT_NOT_HELD",
                       f"recorded as a proposal: arming {name} spends resources without "
                       f"anyone watching, so it needs {grant}, which this actor does not "
                       "hold. The switch did not move.", entry)

    before = path.read_text(encoding="utf-8")
    after = _rewrite(before, wanted)
    path.write_text(after, encoding="utf-8", newline="\n")
    entry = changelog.record(
        schedule=name, change=changelog.SWITCH, direction=direction,
        from_enabled=declared.enabled,
        to_enabled=wanted, actor_id=actor.actor_id, actor_kind=actor.actor_kind,
        binding=actor.binding, reason=reason, occurred_at=now,
        outcome=changelog.EFFECTED, before_digest=changelog.digest_text(before),
        after_digest=changelog.digest_text(after))
    changelog.append(root, entry)
    return Outcome(changelog.EFFECTED, name, direction, None,
                   f"{name} is now {_word(wanted)}. The declaration is changed in the "
                   "working tree and not committed; nothing ticks it yet.", entry)


def _word(enabled: bool) -> str:
    """`armed` rather than `running`: nothing on this node ticks a schedule."""
    return "armed" if enabled else "off"


#: The top-level ``enabled`` line, at the two-space indent every declaration uses.
_ENABLED_LINE = re.compile(r'^  "enabled": (?:true|false)(,?)$', re.MULTILINE)


def _rewrite(text: str, enabled: bool) -> str:
    """Set ``enabled`` and leave every other byte alone.

    A one-line substitution rather than a reserialise, because these declarations are
    hand-written and hold formatting that ``json.dumps`` does not reproduce - an inline
    ``args`` object expands to five lines, and the switch diff then buries its own one
    changed field in a reformat of the whole file. Nobody reviews that diff.

    The substitution is verified rather than trusted: the result is re-parsed and
    compared field by field against the original, and anything but ``enabled`` moving
    is a bug in this function, not a declaration to write. It falls back to a full
    reserialise only when the file does not carry the expected line at all.
    """
    before = json.loads(text)
    after = dict(before)
    after["enabled"] = enabled
    patched, count = _ENABLED_LINE.subn(
        lambda match: f'  "enabled": {str(enabled).lower()}{match.group(1)}', text, count=1)
    if count == 1 and json.loads(patched) == after:
        return patched
    return json.dumps(after, indent=2, ensure_ascii=False) + "\n"
