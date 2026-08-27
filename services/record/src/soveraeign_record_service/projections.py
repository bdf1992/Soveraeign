"""Rebuildable views over the journal, and the refusal that keeps them views.

`core.py` owns the journal: appending to it, and verifying that what it holds is
what was written. This owns everything derived from it, which is a different kind
of thing — a projection is dropped and rebuilt from the journal alone, so it can
be wrong without the record being wrong, and it is never the answer to a question
about what happened.

`append_from_projection` is here rather than beside the append path on purpose.
The shortcut it refuses is promoting derived state back into the record, and the
refusal belongs with the derived state that would tempt someone into it.

Split out of `core.py` when requiring canonical payload bytes during verification
took that module past the 300-line limit.
"""

from __future__ import annotations

from typing import Any


class ProjectionSurface:
    """The journal's derived views, mixed into ``RecordService``.

    The attributes used here — ``db``, and the journal reads ``reconstruct`` and
    ``entries`` — belong to ``RecordService``. This is never instantiated alone;
    it exists to keep what is derived separable from what is recorded.
    """

    def drop_projections(self) -> None:
        """Delete every projection. Only projections are ever deleted here."""
        self.db.execute("DELETE FROM subject_projection")
        self.db.commit()

    def rebuild_projections(self) -> int:
        """Rebuild every projection from the journal alone."""
        from soveraeign_record_service.core import GENESIS

        self.drop_projections()
        state: dict[str, dict[str, Any]] = {}
        countered: set[str] = set()
        for entry in self.reconstruct():
            if entry["kind"] == "COUNTER":
                countered.add(entry["payload"]["counters"])
            row = state.setdefault(
                entry["subject"],
                {"entry_count": 0, "last_kind": entry["kind"], "countered": 0,
                 "head_digest": GENESIS},
            )
            row["entry_count"] += 1
            row["last_kind"] = entry["kind"]
            row["head_digest"] = entry["entry_digest"]
        for entry in self.entries():
            if entry["entry_id"] in countered:
                state[entry["subject"]]["countered"] += 1
        self.db.executemany(
            "INSERT INTO subject_projection VALUES(?,?,?,?,?)",
            [(subject, row["entry_count"], row["last_kind"], row["countered"],
              row["head_digest"]) for subject, row in state.items()],
        )
        self.db.commit()
        return len(state)

    def projection(self, subject: str) -> dict[str, Any]:
        """Read one projection row. Rebuildable, never authoritative."""
        from soveraeign_record_service.core import UnknownEntry

        row = self.db.execute(
            "SELECT * FROM subject_projection WHERE subject=?", (subject,)
        ).fetchone()
        if row is None:
            raise UnknownEntry(subject)
        return dict(row)

    def append_from_projection(self, *_: Any, **__: Any) -> None:
        """Refuse the convenient shortcut of promoting a projection to the record."""
        from soveraeign_record_service.core import ProjectionNotAuthoritative

        raise ProjectionNotAuthoritative(
            "a projection is rebuildable and never authoritative; "
            "re-enter the claim as a proposal through the transition contract"
        )


__all__ = ["ProjectionSurface"]
