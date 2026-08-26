"""Session cards and inspectors, built from the harness snapshot and nothing else.

The records come from ``scripts/sov_session.py list --json`` through
``session_presence``. This module normalizes them into Collection records; it
reads no store, opens no file, and adds no field the harness did not report.

Two rules shape every choice here. A field the source omitted is reported as not
reported, never defaulted to a plausible value; and host presence stays HARNESS
state, so no session card ever carries a Node affordance, authority, or standing.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sovsurface.collection import Affordance, Collection, Record
from sovsurface.primitives import code, e
from sovsurface.session_inspector import NOT_REPORTED, SOURCE, sections

FACETS = (
    "kind",
    "live",
    "branch",
    "principal",
    "verification",
    "has",
    "resource",
    "tree",
)

OMISSIONS = (
    "Authority is not a session field. The harness registry records coordination, "
    "so no card can say what a session is permitted to do.",
    "Pull request and issue relations are not read: no session field records them, "
    "and deriving one from the branch name would be a guess.",
)


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _token(value: str) -> str:
    """A facet value must be one whitespace-free token or it cannot be queried."""
    return value if value and not any(char.isspace() for char in value) else ""


def _claims(snapshot: dict[str, Any], session: str) -> list[str]:
    """Paths this session currently holds, read from the snapshot's own claim map."""
    held = snapshot.get("held")
    if not isinstance(held, dict):
        return []
    paths: list[str] = []
    for path, holders in held.items():
        if not isinstance(holders, list):
            continue
        if any(
            isinstance(holder, dict) and holder.get("session") == session
            for holder in holders
        ):
            paths.append(str(path))
    return sorted(paths)


def queryable(claims: Sequence[str]) -> tuple[str, ...]:
    """The claims a query can actually address.

    A path carrying whitespace cannot be one query token, so it is shown in the
    inspector and left out of the facet. An affordance built from the unfiltered
    list would offer a filter that matches nothing and blank the workspace.
    """
    return tuple(filter(None, (_token(path) for path in claims)))


def _facets(item: dict[str, Any], claims: Sequence[str]) -> dict[str, tuple[str, ...]]:
    live = bool(item.get("live"))
    principal, verification = _text(item.get("principal")), _text(item.get("verification"))
    intent = _text(item.get("intent"))
    facets: dict[str, tuple[str, ...]] = {
        "kind": ("session",),
        "live": ("true" if live else "false",),
    }
    for key, value in (
        ("branch", _text(item.get("branch"))),
        ("principal", principal),
        ("verification", verification),
        ("tree", _text(item.get("tree")).rstrip("/\\")),
    ):
        token = _token(value)
        if token:
            facets[key] = (token,)
    has = [name for name, present in (
        ("claim", bool(claims)),
        ("intent", bool(intent)),
        ("principal", bool(principal)),
        ("verification", bool(verification)),
    ) if present]
    if has:
        facets["has"] = tuple(has)
    resources = queryable(claims)
    if resources:
        facets["resource"] = resources
    return facets


def record(
    item: dict[str, Any],
    snapshot: dict[str, Any],
    peers: Sequence[dict[str, Any]],
) -> Record:
    """Normalize one harness session into a Collection record."""
    session = _text(item.get("session")) or "unnamed-session"
    live = bool(item.get("live"))
    claims = _claims(snapshot, session)
    branch = _text(item.get("branch"))
    intent = _text(item.get("intent"))
    addressable = queryable(claims)
    tree = _token(_text(item.get("tree")).rstrip("/\\"))
    badges: list[tuple[str, str]] = [
        ("HARNESS", "warning"),
        ("live", "positive") if live else ("not live", "muted"),
    ]
    if claims:
        badges.append((f"{len(claims)} claims", "muted"))
    summary = (
        f'<div class="card-statline">{code(branch) if branch else NOT_REPORTED}</div>'
        f'<p class="muted">{e(intent) if intent else "no intent recorded"}</p>'
    )
    search = " ".join(
        filter(
            None,
            (
                session,
                branch,
                intent,
                _text(item.get("principal")),
                _text(item.get("verification")),
                _text(item.get("tree")),
                *claims,
            ),
        )
    )
    return Record(
        identity=session,
        kind="session",
        title=session,
        eyebrow="harness session",
        summary=summary,
        badges=tuple(badges),
        search=search,
        facets=_facets(item, claims),
        sections=sections(item, claims, peers),
        affordances=(
            Affordance(
                "Filter to this session's claims",
                filter_value=f"resource:{addressable[0]}" if addressable else "",
                detail=(
                    "Query narrows what is shown. It changes no claim."
                    if addressable
                    else "This session holds no claim a single query token can address."
                ),
                available=bool(addressable),
            ),
            Affordance(
                "Filter to sessions in this working tree",
                filter_value=f"tree:{tree}" if tree else "",
                detail="Query narrows what is shown.",
                available=bool(tree),
            ),
            Affordance(
                "Act as this session",
                detail="No Node operation is reachable from harness presence.",
                available=False,
            ),
        ),
        omissions=() if live else ("The source reports this session as not live.",),
    )


def collection(snapshot: dict[str, Any]) -> Collection:
    """Build the Sessions collection from one harness snapshot."""
    if not snapshot.get("available"):
        return Collection(
            collection_id="sessions",
            label="Sessions",
            description="Live host sessions inhabiting this repository.",
            source=str(snapshot.get("source") or SOURCE),
            facets=FACETS,
            available=False,
            unavailable_reason=str(snapshot.get("reason") or "source not readable"),
            omissions=OMISSIONS,
        )
    items = [item for item in snapshot.get("records", ()) if isinstance(item, dict)]
    if not items:
        items = [item for item in snapshot.get("sessions", ()) if isinstance(item, dict)]
    items.sort(key=lambda item: (not item.get("live"), _text(item.get("session"))))
    return Collection(
        collection_id="sessions",
        label="Sessions",
        description=(
            "Host sessions as the SOV session registry reports them. Presence is "
            "coordination state, not Node standing."
        ),
        source=str(snapshot.get("source") or SOURCE),
        records=tuple(record(item, snapshot, items) for item in items),
        facets=FACETS,
        layout="grid",
        omissions=OMISSIONS,
    )


def presence_panel(built: Collection) -> str:
    """A compact utility-drawer presence readout over the same collection.

    Presence is a summary of the cards, never a second reading of the source, so
    the drawer and the workspace can never disagree about who is here.
    """
    if not built.available:
        return (
            '<h2>Presence</h2><div class="panel omission" data-component="presence">'
            '<div class="eyebrow">HARNESS · unavailable</div>'
            f'<p class="muted">{e(built.unavailable_reason)}</p>'
            f"<p>{code(built.source)}</p></div>"
        )
    live = built.facet_values("live").get("true", 0)
    rows = "".join(
        f'<div class="utility-row"><span>{e(item.identity)}</span>'
        f'<b>{"live" if "true" in item.facets.get("live", ()) else "not live"}</b></div>'
        for item in built.records
    )
    return (
        '<h2>Presence</h2><div class="panel" data-component="presence">'
        '<div class="eyebrow">HARNESS · host coordination</div>'
        f'<div class="utility-row"><span>live now</span><b>{live}</b></div>'
        f'<div class="utility-row"><span>known</span><b>{len(built.records)}</b></div>'
        f'{rows}<p class="muted">Presence grants no authority, standing, route, or '
        'Node observation.</p>'
        '<button class="text-action" type="button" data-filter="kind:session">'
        "Browse sessions</button></div>"
    )
