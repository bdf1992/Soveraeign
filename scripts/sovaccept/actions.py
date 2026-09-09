"""One checked acceptance transition, including repeat delivery of its response."""

from __future__ import annotations

import re
from pathlib import Path

from sovaccept import ledger, policy, review


def record(root: Path, packet_id: str, action: str, seat_id: str, actor_id: str,
           when: str, note: str | None, reviewed: str | None) -> dict:
    """Record a fresh decision or return the unchanged receipt for an exact retry.

    Time is not request identity. A changed action, actor, seat or note is a new
    request and cannot overwrite a decision. Historical unpinned acts block reuse.
    """
    from sovaccept import packet as packets

    if not re.fullmatch(r"A[0-9]+", packet_id):
        raise review.AcceptanceError("PACKET_INCOMPLETE: invalid packet identifier")
    with ledger.locked(root) as path:
        original, entries = ledger.read(path)
        prior = [entry for entry in entries if entry["packet_id"] == packet_id]
        if prior:
            if len(prior) == 1:
                entry = prior[0]
                same = (reviewed is not None
                        and entry.get("review", {}).get("review_digest") == reviewed
                        and entry.get("action") == action
                        and entry.get("accepted_by_seat") == seat_id
                        and entry.get("actor_id") == actor_id
                        and entry.get("note") == note)
                if same:
                    return entry
            raise review.AcceptanceError(
                "ALREADY_ACTED: this packet has a decision; a changed decision needs a new packet")
        if not reviewed:
            raise review.AcceptanceError("REVIEW_REQUIRED: present the packet and pass its --review token")
        packet = packets.load(root, packet_id)
        problems = [str(defect) for defect in policy.audit_packet(root, packet)]
        if problems:
            raise review.AcceptanceError("\n".join(problems))
        problems = packets.refusals(root, packet, action, seat_id, actor_id)
        if problems:
            raise review.AcceptanceError("\n".join(problems))
        identity = review.capture(root, packet)
        if identity["review_digest"] != reviewed:
            raise review.AcceptanceError(
                "STALE_REVIEW: the packet or subject changed; review the current presentation")
        entry = {
            "recorded_at": when, "packet_id": packet_id, "claim": packet["claim"],
            "artifact": packet["subject"]["artifact"], "action": action,
            "presented_by_seat": packet["presented_by_seat"], "accepted_by_seat": seat_id,
            "claim_type": packet["claim_type"], "actor_id": actor_id, "note": note,
            "effect_class": "RECORD_LOCAL",
            "standing_change_lands_in": packet["subject"]["artifact"],
            "review": identity, "packet": packet,
        }
        ledger.append(path, original, entry)
        return entry
