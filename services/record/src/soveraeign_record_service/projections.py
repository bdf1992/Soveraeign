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

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Iterable
import json

from .errors import ProjectionNotAuthoritative, UnknownEntry


def _projection_digest(payload: dict[str, Any]) -> str:
    """Digest a projection basis independently of the time somebody reads it."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def _cutoff_time(recorded_at: float) -> str:
    """Use the cutoff row's recorded time so rebuilding the same view is stable."""
    return datetime.fromtimestamp(recorded_at, timezone.utc).isoformat().replace("+00:00", "Z")


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
        row = self.db.execute(
            "SELECT * FROM subject_projection WHERE subject=?", (subject,)
        ).fetchone()
        if row is None:
            raise UnknownEntry(subject)
        return dict(row)

    def evidence_projection(
        self,
        subjects: Iterable[str],
        recipient_principal: str,
        recipient_relation: str,
        purpose: str,
        *,
        as_of_entry: str | None = None,
        exclude_kinds: Iterable[str] = (),
    ) -> dict[str, Any]:
        """Derive one frozen evidence reading of the common Record.

        The returned object matches ``contracts/record-projection.schema.json``.
        It contains addresses and digests, not copied persuasive conclusions, and
        is deterministic for one verified journal, request and cutoff. The caller
        names the recipient relation; this service records no identity or authority
        claim on its behalf.
        """
        requested = tuple(dict.fromkeys(str(item) for item in subjects if str(item)))
        if not requested:
            raise ValueError("at least one subject is required")
        if not recipient_principal or not recipient_relation or not purpose:
            raise ValueError("recipient principal, relation, and purpose are required")
        excluded = tuple(dict.fromkeys(str(item) for item in exclude_kinds if str(item)))
        invalid = sorted(set(excluded) - {"EVENT", "RECEIPT", "OBSERVATION", "COUNTER"})
        if invalid:
            raise ValueError("unknown excluded record kind(s): " + ", ".join(invalid))

        replayed = self.reconstruct()
        if not replayed:
            raise UnknownEntry("journal is empty")
        if as_of_entry is None:
            cutoff_index = len(replayed) - 1
        else:
            cutoff_index = next(
                (index for index, entry in enumerate(replayed)
                 if entry["entry_id"] == as_of_entry), -1)
            if cutoff_index < 0:
                raise UnknownEntry(as_of_entry)
        cutoff = replayed[cutoff_index]
        bounded = replayed[:cutoff_index + 1]
        matching = [entry for entry in bounded if entry["subject"] in requested]
        included = [entry for entry in matching if entry["kind"] not in excluded]
        if not included:
            raise UnknownEntry("no included records for requested subjects at cutoff")

        omissions = []
        for kind in excluded:
            if any(entry["kind"] == kind for entry in matching):
                omissions.append({
                    "record_class": kind,
                    "reason": "excluded by the projection request",
                })

        basis = {
            "record_projection_schema": "soveraeign-record-projection/v1",
            "subject_addresses": list(requested),
            "recipient_principal": recipient_principal,
            "recipient_relation": recipient_relation,
            "purpose": purpose,
            "record_head": "sha256:" + cutoff["entry_digest"],
            "as_of": "record:" + cutoff["entry_id"],
            "included_records": [
                {"address": "record:" + entry["entry_id"],
                 "digest": "sha256:" + entry["entry_digest"]}
                for entry in included
            ],
            "omissions": omissions,
            "authority_effect": "NONE",
            "created_at": _cutoff_time(float(cutoff["recorded_at"])),
        }
        digest = _projection_digest(basis)
        return {
            **basis,
            "projection_id": "urn:soveraeign:record-projection:" + digest,
            "projection_digest": "sha256:" + digest,
        }

    def append_from_projection(self, *_: Any, **__: Any) -> None:
        """Refuse the convenient shortcut of promoting a projection to the record."""
        raise ProjectionNotAuthoritative(
            "a projection is rebuildable and never authoritative; "
            "re-enter the claim as a proposal through the transition contract"
        )


__all__ = ["ProjectionSurface"]
