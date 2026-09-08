"""Is one actor a version of another? The perspective axis, in one place.

`decisions/0104-independence-is-context-and-perspective.md`, Ruling 3: the same actor is the
same perspective, and a later session holding none of the prior transcript is a version of the
prior actor rather than a stranger to it. What carries the frame is the operating profile an
actor loaded, not its id, because a rename defeats an id and does not defeat a frame.

This lives apart from `relation.py` because two callers need it and an independent witness
found them drifting: the walk compared profiles while `observe.py`'s relay refusal compared
ids, so one module called two actors the same and the other called them different on the same
record. One reading, one module.
"""

from __future__ import annotations

from .record import RunRecord

#: `_version_of` outcomes. UNKNOWN is the answer that must never read as "different".
SAME, DIFFERENT, UNKNOWN = "SAME", "DIFFERENT", "UNKNOWN"


def _version_of(record: RunRecord, candidate: str, actor: str) -> str:
    """Is the candidate a version of this actor: the same id, or the same loaded profile?

    Three answers, for the reason the whole service has three outcomes. Equal ids are `SAME`
    without reading a profile at all. Different ids over two profiles the record carries are
    `DIFFERENT`. Different ids where either profile is missing are `UNKNOWN`: a rename is
    exactly what the profile exists to defeat, so absence of a profile is absence of an
    answer, never a denial.

    An independent witness found the earlier two-valued version of this reading `INDEPENDENT`
    for a candidate that had loaded the builder's profile under another id, because the prior
    arrow's actor carried no launch entry. That is the failure Ruling 3 exists to close.
    """
    if candidate == actor:
        return SAME
    theirs = record.profile_of(actor)
    ours = record.profile_of(candidate)
    if theirs is None or ours is None:
        return UNKNOWN
    return SAME if theirs == ours else DIFFERENT



def is_version_of_any(record: RunRecord, candidate: str, actors) -> bool:
    """Is the candidate the same version as any of these actors, or unprovably distinct?

    True on `SAME` and on `UNKNOWN`. Callers use this to refuse, so an unreadable record must
    not answer "different".
    """
    return any(_version_of(record, candidate, actor) != DIFFERENT for actor in actors)


__all__ = ["DIFFERENT", "SAME", "UNKNOWN", "is_version_of_any"]
