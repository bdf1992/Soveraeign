"""Compose the Human Binding workspace out of Collections.

Every section of the workspace is a Collection over records that already exist:
the canonical Node Interface for services, subjects, and operations, and the SOV
session harness for sessions. This module lays them out and adds no record, no
route, no authority, and no standing of its own.

Node state and HARNESS state are composed side by side and never merged. A
session card is labelled HARNESS wherever it appears, and no arrangement of
cards turns host presence into a governed Node fact.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from sovsurface import sessions as session_cards
from sovsurface.catalog import operation_collection, service_collection, subject_collection
from sovsurface.collection import Collection, counts, facet_manifest
from sovsurface.collection import render as render_collection
from sovsurface.primitives import badge, e, empty_state, metric, nav_item, panel, rail_item
from sovsurface.theme import EXTRA, SCRIPT, STYLE

__all__ = ["render", "STYLE", "SCRIPT"]


def _service_map(interface: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    services: dict[str, list[dict[str, Any]]] = {}
    for operation in interface["operations"]:
        services.setdefault(operation["service_id"], []).append(operation)
    return services


def _subject_map(interface: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    subjects: dict[str, list[dict[str, Any]]] = {}
    for operation in interface["operations"]:
        subjects.setdefault(operation["subject"], []).append(operation)
    return subjects


def _rail(services: dict[str, list[dict[str, Any]]]) -> str:
    items = [rail_item("Node home", short="S", active=True), '<div class="rail-sep"></div>']
    items.extend(
        rail_item(f"{service} service", short=service, filter_value=f"service:{service}")
        for service in sorted(services)
    )
    items.append('<div class="rail-sep"></div>')
    items.append(rail_item("Host sessions", short="SE", filter_value="kind:session"))
    return f'<aside class="rail" data-component="service-rail">{"".join(items)}</aside>'


def _nav(
    interface: dict[str, Any],
    services: dict[str, list[dict[str, Any]]],
    session_collection: Collection,
) -> str:
    kinds = Counter(item["affordance"]["kind"] for item in interface["operations"])
    live = session_collection.facet_values("live").get("true", 0)
    rows = [
        nav_item("Everything", icon="⌂", active=True, count=len(interface["operations"])),
        nav_item("Actions", icon="▶", count=kinds["ACTION"], filter_value="affordance:ACTION"),
        nav_item("Reads", icon="↳", count=kinds["READ"], filter_value="affordance:READ"),
        nav_item("Inspect", icon="◇", count=kinds["INSPECT"], filter_value="affordance:INSPECT"),
    ]
    service_rows = [
        nav_item(service, icon="#", count=len(ops), filter_value=f"service:{service}")
        for service, ops in sorted(services.items())
    ]
    node = interface["node"]
    return (
        '<aside class="nav" data-component="browser-nav">'
        f'<div class="node-name"><b>{e(node["display_name"])}</b>'
        f'<span>{e(node["node_id"])} · {e(node["root_seat"])}</span></div>'
        '<div class="section-label">Browse</div>'
        + "".join(rows)
        + '<div class="section-label">Services</div>'
        + "".join(service_rows)
        + '<div class="section-label">Assets &amp; subjects</div>'
        + nav_item("Asset service", icon="▣", filter_value="service:asset")
        + nav_item("Declared subjects", icon="◆", filter_value="kind:subject")
        + '<div class="section-label">Host harness</div>'
        + nav_item(
            "Sessions",
            icon="◉",
            count=len(session_collection.records),
            filter_value="kind:session",
        )
        + nav_item("Live now", icon="●", count=live, filter_value="live:true")
        + nav_item("Holding paths", icon="⛨", filter_value="has:claim")
        + "</aside>"
    )


def _utility(interface: dict[str, Any], session_collection: Collection) -> str:
    kinds = Counter(item["affordance"]["kind"] for item in interface["operations"])
    exposure = "".join(
        f'<div class="utility-row"><span>{e(kind)}</span><b>{count}</b></div>'
        for kind, count in sorted(kinds.items())
    )
    omissions = "".join(
        f'<div class="panel omission"><h3>{e(item["code"])}</h3>'
        f'<p class="muted">{e(item["explanation"])}</p></div>'
        for item in interface["omissions"]
    )
    help_body = (
        '<div class="query-help">'
        "<code>service:asset</code><code>affordance:ACTION</code>"
        "<code>subject:Asset</code><code>authority:read:registry</code>"
        "<code>kind:session</code><code>live:true</code><code>has:claim</code>"
        "<code>branch:main</code><code>verification:UNVERIFIED</code></div>"
    )
    return (
        '<aside class="utility" data-component="utility-drawer">'
        "<h2>What this node exposes</h2>"
        f'<div class="panel"><div class="utility-list">{exposure}</div></div>'
        "<h2>Query grammar</h2>"
        + panel("Filter the same records", help_body, eyebrow="search")
        + session_cards.presence_panel(session_collection)
        + "<h2>Material omissions</h2>"
        + omissions
        + "</aside>"
    )


def _hero(interface: dict[str, Any], session_collection: Collection) -> str:
    figures = interface["counts"]
    live = session_collection.facet_values("live").get("true", 0)
    presence = (
        metric(live, "live host sessions", "HARNESS state, not Node standing")
        if session_collection.available
        else metric("—", "live host sessions", "session source unavailable")
    )
    return (
        '<div class="hero"><div class="hero-copy">'
        '<div class="eyebrow">human binding · composed view</div>'
        "<h2>One Node, browsable like a workspace.</h2>"
        "<p>Rail, navigator, collections, query, facets, cards, selection, inspector, "
        "affordances, presence, and utilities are presentation primitives over records "
        "that already exist. Layout cannot manufacture reachability, authority, "
        "standing, or object instances.</p></div>"
        '<div class="metrics">'
        + metric(figures["declared"], "declared operations")
        + metric(figures["reachable"], "exact routes")
        + metric(figures["observed"], "admitted observations")
        + presence
        + "</div></div>"
    )


def _toolbar() -> str:
    pills = (
        ("All cards", ""),
        ("Services", "kind:service"),
        ("Subjects", "kind:subject"),
        ("Operations", "kind:operation"),
        ("Sessions", "kind:session"),
        ("Live sessions", "live:true"),
        ("Callable actions", "affordance:ACTION"),
    )
    buttons = "".join(
        f'<button class="pill{" active" if not value else ""}" '
        f'data-filter="{e(value)}" type="button">{e(label)}</button>'
        for label, value in pills
    )
    return f'<div class="toolbar" data-component="filter-pills">{buttons}</div>'


def collections(interface: dict[str, Any], presence: dict[str, Any] | None) -> list[Collection]:
    """Every collection the workspace renders, in reading order."""
    return [
        session_cards.collection(presence or {"available": False, "reason": "not read"}),
        service_collection(_service_map(interface)),
        subject_collection(_subject_map(interface)),
        operation_collection(interface["operations"]),
    ]


def _main(interface: dict[str, Any], built: list[Collection], session: Collection) -> str:
    sections = "".join(render_collection(item) for item in built)
    return (
        '<main class="main" data-component="workspace">'
        + _hero(interface, session)
        + _toolbar()
        + sections
        + '<div data-no-results hidden>'
        + empty_state("No cards match", "Change the query or clear filters.")
        + "</div></main>"
    )


def render(interface: dict[str, Any], presence: dict[str, Any] | None = None) -> str:
    """Render the composed shell over the canonical interface and host presence.

    ``presence`` is the harness snapshot. Omitting it renders the sessions
    collection as an explicit unavailable state; it never renders as empty.
    """
    services = _service_map(interface)
    built = collections(interface, presence)
    session = built[0]
    node = interface["node"]
    totals = counts(built)
    top = (
        '<header class="topbar" data-component="command-bar">'
        f'<h1>{e(node["display_name"])}</h1>{badge("projection only")}'
        '<div class="search"><input data-query aria-label="Filter Node and harness cards" '
        'placeholder="Search or filter: service:asset  kind:session  live:true"><kbd>Ctrl K</kbd></div>'
        '<span class="result-count" data-result-count></span></header>'
    )
    status = (
        '<footer class="status">NODE INTERFACE · '
        f'{e(interface["input_state_digest"])} · '
        f'{totals["operations"]} operations · {totals["sessions"]} harness sessions · '
        "rendering grants nothing · not an observation</footer>"
    )
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Soveraeign Composable Human Surface</title>"
        f"<style>{STYLE}{EXTRA}</style></head><body>"
        + facet_manifest(built)
        + '<div class="shell">'
        + _rail(services)
        + _nav(interface, services, session)
        + top
        + _main(interface, built, session)
        + _utility(interface, session)
        + status
        + f"</div><script>{SCRIPT}</script></body></html>"
    )
