"""A reusable Collection projection for the Human Binding surface.

A Collection is a discardable view over records that already exist somewhere
else. It owns no state, is never a System of Record, and adds no meaning to the
records it carries: it only decides what is searchable, what is filterable, what
a card shows, and what an inspector expands.

Every collection declares its own source and its own material omissions, so a
reader can always ask where a card came from and what the source did not say.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import json
import re

from sovsurface.primitives import badge, e, empty_state

FACET_KEY = re.compile(r"^[a-z][a-z0-9]*$")
"""Facet keys become ``data-<key>`` attributes read back through ``dataset``.

A hyphen or an underscore is case-folded by the DOM and would silently stop
matching, so the grammar refuses anything but a lowercase single word.
"""


RESERVED = frozenset({"card", "kind", "identity", "search"})
"""Attributes a card always carries structurally.

``data-kind`` is emitted from the record's own kind, so a facet of the same name
would emit the attribute twice and the browser would silently keep the first.
These keys stay declarable — the query script must know ``kind:`` filters — but
the attribute is written once, from the record.
"""


class FacetError(ValueError):
    """A collection declared a facet the query grammar cannot address."""


@dataclass(frozen=True)
class Section:
    """One inspector section: a title, ordered label/value rows, and a caveat."""

    title: str
    rows: tuple[tuple[str, str], ...] = ()
    note: str = ""


@dataclass(frozen=True)
class Affordance:
    """Something a reader may do from a card, and whether it is available here.

    An affordance that is not ``available`` renders as stated-and-refused. The
    surface never hides an unreachable action, and never makes one reachable.
    """

    label: str
    detail: str = ""
    filter_value: str = ""
    command: str = ""
    available: bool = True


@dataclass(frozen=True)
class Record:
    """One normalized row: identity, kind, search text, facets, card, inspector.

    ``identity``, ``title``, ``eyebrow``, ``search``, ``omissions``, and every
    facet value are escaped by the renderer. ``summary`` and every ``Section``
    row value are inserted as HTML: an adapter composes them with ``code()`` and
    ``e()`` and owns their escaping. Never pass a raw source string to either.
    """

    identity: str
    kind: str
    title: str
    eyebrow: str = ""
    summary: str = ""
    badges: tuple[tuple[str, str], ...] = ()
    search: str = ""
    facets: Mapping[str, Sequence[str]] = field(default_factory=dict)
    sections: tuple[Section, ...] = ()
    affordances: tuple[Affordance, ...] = ()
    omissions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        declared = tuple(self.facets.get("kind", ()))
        if declared and declared != (self.kind,):
            raise FacetError(
                f"record {self.identity!r} declares kind facet {declared!r} but is a "
                f"{self.kind!r} card; the query would disagree with the record"
            )


@dataclass(frozen=True)
class Collection:
    """A named set of records read from one declared source."""

    collection_id: str
    label: str
    description: str
    source: str
    records: tuple[Record, ...] = ()
    facets: tuple[str, ...] = ()
    layout: str = "grid"
    available: bool = True
    unavailable_reason: str = ""
    omissions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for key in self.facets:
            if not FACET_KEY.match(key):
                raise FacetError(f"facet key {key!r} is not a lowercase single word")

    def facet_values(self, key: str) -> dict[str, int]:
        """Count how many records carry each value of one declared facet."""
        counts: dict[str, int] = {}
        for record in self.records:
            for value in record.facets.get(key, ()):
                counts[value] = counts.get(value, 0) + 1
        return dict(sorted(counts.items()))


def _facet_attributes(record: Record, declared: Sequence[str]) -> str:
    """Emit only declared facets, space-joined, so a query matches whole tokens."""
    parts: list[str] = []
    for key in declared:
        values = record.facets.get(key)
        if not values or key in RESERVED:
            continue
        parts.append(f'data-{key}="{e(" ".join(str(item) for item in values))}"')
    return (" " + " ".join(parts)) if parts else ""


def _rows_html(rows: Iterable[tuple[str, str]]) -> str:
    body = "".join(f"<dt>{e(label)}</dt><dd>{value}</dd>" for label, value in rows)
    return f'<dl class="facts">{body}</dl>' if body else ""


def render_sections(sections: Sequence[Section]) -> str:
    """Render an inspector from the same record that produced the card."""
    blocks: list[str] = []
    for section in sections:
        note = f'<p class="boundary">{e(section.note)}</p>' if section.note else ""
        body = _rows_html(section.rows) or '<p class="muted">nothing reported</p>'
        blocks.append(
            '<div class="inspector-section" data-component="inspector-section">'
            f'<div class="eyebrow">{e(section.title)}</div>{body}{note}</div>'
        )
    return "".join(blocks)


def render_affordances(affordances: Sequence[Affordance]) -> str:
    """Render affordances without granting any of them."""
    if not affordances:
        return ""
    rendered: list[str] = []
    for item in affordances:
        if item.available and item.filter_value:
            control = (
                '<button class="text-action" type="button" '
                f'data-filter="{e(item.filter_value)}">{e(item.label)}</button>'
            )
        elif item.available and item.command:
            control = f'<pre class="command">{e(item.command)}</pre>'
        else:
            control = f'<span class="badge warning">{e(item.label)} unavailable</span>'
        detail = f'<span class="boundary">{e(item.detail)}</span>' if item.detail else ""
        rendered.append(f'<div class="affordance">{control}{detail}</div>')
    return (
        '<div class="inspector-section" data-component="affordances">'
        '<div class="eyebrow">Affordances</div>' + "".join(rendered) + "</div>"
    )


def render_record(record: Record, declared: Sequence[str], *, layout: str) -> str:
    """Render one card whose inspector expands from the same record."""
    badges = "".join(badge(label, tone) for label, tone in record.badges)
    eyebrow = f'<div class="eyebrow">{e(record.eyebrow)}</div>' if record.eyebrow else ""
    omissions = "".join(
        f'<div class="omission-note">{e(item)}</div>' for item in record.omissions
    )
    inspector = render_sections(record.sections) + render_affordances(record.affordances)
    body = (
        f'<div class="card-body">{record.summary}{omissions}'
        f'<div class="inspector" data-component="inspector">{inspector}</div></div>'
    )
    return (
        f'<details class="card {e(layout)}-card" data-card="{e(record.kind)}" '
        f'data-kind="{e(record.kind)}" data-identity="{e(record.identity)}" '
        f'data-search="{e(record.search.lower())}"'
        f"{_facet_attributes(record, declared)}>"
        f'<summary><span class="card-leading">{eyebrow}'
        f'<span class="card-title">{e(record.title)}</span></span>'
        f'<span class="badges">{badges}</span></summary>'
        f"{body}</details>"
    )


def render(collection: Collection) -> str:
    """Render a whole collection, including its unavailable and empty states."""
    header = (
        f"<header><h2>{e(collection.label)}</h2>"
        f"<p>{e(collection.description)}</p></header>"
    )
    provenance = (
        '<div class="provenance" data-component="provenance">'
        f'<span>source</span><code>{e(collection.source)}</code></div>'
    )
    omissions = "".join(
        '<div class="panel omission" data-component="omission">'
        '<div class="eyebrow">material omission</div>'
        f'<p class="muted">{e(item)}</p></div>'
        for item in collection.omissions
    )
    if not collection.available:
        body = empty_state(
            f"{collection.label} unavailable",
            collection.unavailable_reason or "the declared source could not be read",
            code_value=collection.source,
        )
    elif not collection.records:
        body = empty_state(
            f"No {collection.label.lower()}",
            "The source was read and reported nothing. That is an empty source, "
            "not a missing one.",
            code_value=collection.source,
        )
    else:
        cards = "".join(
            render_record(record, collection.facets, layout=collection.layout)
            for record in collection.records
        )
        container = "card-grid" if collection.layout == "grid" else "card-rows"
        body = f'<div class="{container}">{cards}</div>'
    return (
        f'<section class="surface-section" data-collection="{e(collection.collection_id)}">'
        f"{header}{provenance}{omissions}{body}</section>"
    )


def facet_manifest(collections: Sequence[Collection]) -> str:
    """Declare every filterable key to the query script as data, not as code."""
    keys = sorted({key for collection in collections for key in collection.facets})
    return (
        '<script type="application/json" data-facet-keys>'
        + json.dumps(keys, separators=(",", ":"))
        + "</script>"
    )


def counts(collections: Sequence[Collection]) -> dict[str, int | None]:
    """Card totals per collection, or None where the source was never read.

    Zero is a claim: it says the source was read and reported nothing. A source
    that could not be read has no count, so an unavailable collection returns
    None and every caller has to decide how to say "not read" out loud.
    """
    return {
        item.collection_id: (len(item.records) if item.available else None)
        for item in collections
    }


def cards_total(collections: Sequence[Collection]) -> int:
    """Every card the workspace will render, across every readable collection."""
    return sum(len(item.records) for item in collections if item.available)


def facet_total(collections: Sequence[Collection], key: str, value: str) -> int:
    """How many cards one ``key:value`` query would leave showing.

    A count shown beside a filter is a claim about what that filter does. The
    query matches every card in the page, not the cards of one collection, so a
    count taken over a single collection describes a different population than
    the control it labels and is wrong by exactly the other collections.
    """
    return sum(
        1
        for collection in collections
        if collection.available
        for record in collection.records
        if value in record.facets.get(key, ())
    )
