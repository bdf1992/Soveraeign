"""The session inspector: seven sections built from one harness record.

Every row here restates what the source said. A field the source omitted reads
as not reported rather than as a default, because a plausible default is the way
a surface starts asserting identity, verification, or authority it never read.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sovsurface.collection import Section
from sovsurface.primitives import code, e

SOURCE = "scripts/sov_session.py list --json"

NOT_REPORTED = '<span class="muted">not reported by this source</span>'

BOUNDARY = (
    "HARNESS state. A registered session holds no Node authority, no grant, and no "
    "standing; presence here is host coordination and never a governed observation."
)


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _relations(item: dict[str, Any], peers: Sequence[dict[str, Any]]) -> list[tuple[str, str]]:
    """Co-tenancy derived from the same records, not inferred from anything else."""
    session = _text(item.get("session"))
    tree, branch = _text(item.get("tree")), _text(item.get("branch"))
    same_tree = sorted(
        _text(peer.get("session"))
        for peer in peers
        if _text(peer.get("session")) != session and tree and _text(peer.get("tree")) == tree
    )
    same_branch = sorted(
        _text(peer.get("session"))
        for peer in peers
        if _text(peer.get("session")) != session
        and branch
        and _text(peer.get("branch")) == branch
    )
    return [
        ("Shares this working tree", _peers(tree, same_tree)),
        ("Shares this branch", _peers(branch, same_branch)),
    ]


def _peers(field: str, names: Sequence[str]) -> str:
    """Three different answers, told apart.

    The source did not report the field; the source reported it and no other
    session matches; or these sessions match. Collapsing the middle case into
    ``not reported`` tells the reader the harness withheld what it supplied.
    """
    if not field:
        return NOT_REPORTED
    if not names:
        return '<span class="muted">no other session</span>'
    return ", ".join(code(name) for name in names)


def sections(
    item: dict[str, Any],
    claims: Sequence[str],
    peers: Sequence[dict[str, Any]],
) -> tuple[Section, ...]:
    principal, verification = _text(item.get("principal")), _text(item.get("verification"))
    claim_rows = tuple((path, code("held")) for path in claims)
    return (
        Section(
            "Identity",
            (
                ("Session", code(_text(item.get("session")) or "unnamed")),
                ("Principal", code(principal) if principal else NOT_REPORTED),
                ("Verification", code(verification) if verification else NOT_REPORTED),
                ("Registered", code("yes" if item.get("registered") else "no")),
            ),
            note="" if principal else "This source names sessions; it authenticates none.",
        ),
        Section(
            "Location",
            (
                ("Branch", code(_text(item.get("branch"))) if item.get("branch") else NOT_REPORTED),
                ("Working tree", code(_text(item.get("tree"))) if item.get("tree") else NOT_REPORTED),
                ("Process", code(item.get("pid")) if item.get("pid") else NOT_REPORTED),
            ),
        ),
        Section(
            "Activity",
            (
                ("Live", code("true" if item.get("live") else "false")),
                ("Ended", code("true" if item.get("ended") else "false")),
                ("Last seen", code(_text(item.get("at"))) if item.get("at") else NOT_REPORTED),
                (
                    "Ended at",
                    code(_text(item.get("ended_at"))) if item.get("ended_at") else NOT_REPORTED,
                ),
                ("Intent", e(_text(item.get("intent"))) if item.get("intent") else NOT_REPORTED),
            ),
        ),
        Section(
            "Claims",
            claim_rows,
            note="" if claims else "This session holds no path in the claim log.",
        ),
        Section("Relations", tuple(_relations(item, peers))),
        Section("Authority and standing", (("Boundary", e(BOUNDARY)),)),
        Section("Sources", (("Read through", code(SOURCE)),)),
    )
