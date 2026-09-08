"""Read a subject's standing lifecycle for a prior appearance by this candidate.

Standing moves `OPEN -> BUILT -> WITNESSED -> RATIFIED` and a subject collects actors along
the way, so a walk scoped to one run would admit a builder as its own witness one arrow later.

This is its own module because the question it asks is not the question `relation.py` asks
elsewhere. Every other edge reads a fact about the run. This one reads a fact about the
*subject*, which the run only claims to belong to - and three witness passes each defeated a
different reading of that claim. The two guards below are what survived them, and the comments
say which pass found which, because the next reader will be tempted to remove one.
"""

from __future__ import annotations

from typing import Any

from .record import RunRecord
from .version import DIFFERENT, SAME, UNKNOWN, _version_of

def _corroborated(record: RunRecord, arrows: list[dict[str, Any]]) -> bool:
    """Does an actor of this run appear on the subject the run names?

    The subject is the executor's own word. A subject no actor of this run ever moved is not
    this run's lifecycle, whoever named it.
    """
    executors = record.executors()
    return any(_version_of(record, str(entry.get("actor") or ""), actor) == SAME
               for entry in arrows for actor in executors)


def walk_lifecycle(record: RunRecord, candidate: str, walk: _Walk) -> None:
    """Did the candidate, or a version of it, already move this subject along an arrow?

    Without a subject the run belongs to, there is no lifecycle to walk and the edge is
    unanswerable. That is the shape a per-run inference had for every subject.
    """
    subject = record.subject_id()
    if subject is None:
        walk.cannot_answer("PRIOR_STANDING_ACTOR")
        return
    arrows = record.standings(subject)
    if not arrows:
        walk.cannot_answer("PRIOR_STANDING_ACTOR")
        return
    walk.cite(*arrows)
    readings = [(entry, _version_of(record, candidate, str(entry.get("actor") or "")))
                for entry in arrows]
    for entry, reading in readings:
        if reading == SAME:
            walk.edge("PRIOR_STANDING_ACTOR", entry)
            return

    # Two guards, because three witness passes proved either alone is defeated.
    #
    # The subject is the executor's own word, so it is corroborated: an actor of this run must
    # appear on it, which refuses a decoy pointing at some unrelated lifecycle. Pass 3 then
    # showed the executor satisfies that on any decoy it has itself moved, and the candidate's
    # arrow on the real subject sits in the same record, unread.
    #
    # So the candidate is read across every subject too. Pass 2 objected that this refuses an
    # observer with prior work anywhere, and it does - that cost is real, disclosed in
    # KNOWN-GAPS.md, and accepted, because the alternative pass 3 defeated admits the subject's
    # own builder as its independent observer. Silence is not a pass, and neither is a subject
    # nobody can verify.
    elsewhere = [entry for entry in record.all_standings()
                 if entry.get("subject") != subject
                 and _version_of(record, candidate, str(entry.get("actor") or "")) != DIFFERENT]
    if (not _corroborated(record, arrows) or elsewhere
            or any(reading == UNKNOWN for _, reading in readings)):
        walk.cannot_answer("PRIOR_STANDING_ACTOR")


__all__ = ["walk_lifecycle"]
