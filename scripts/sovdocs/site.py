"""Assemble the rendered documents into one browsable page.

Every document is embedded once and shown one at a time, so the page works from
a file URL with no server, no network, and no external asset. Search runs over
an index built here rather than in the browser, so what a reader searches is the
same text the build read.

The page is a Projection: derived, rebuildable, and never authoritative over the
documents it renders. Where a document's bytes no longer match what the Asset
Service recorded, the page says so on that document rather than quietly showing
newer text under an older provenance.
"""

from __future__ import annotations

from typing import Any
import html
import json

from sovdocs.assets import SCRIPT, STYLE


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _provenance(document: dict[str, Any]) -> str:
    """What the Asset Service holds for this document, and how it got there."""
    record = document.get("asset")
    if not record:
        return ('<p class="prov">Not yet ingested. Run '
                '<code>python scripts/sov_docs.py ingest</code> to give this document '
                'an addressed source and a receipt.</p>')
    drift = record["digest"] != document["digest"]
    versions = record.get("versions") or []
    lines = [f'asset {_e(record["asset_id"])}',
             f'receipt {_e(record["receipt_id"])}',
             f'digest {_e(document["digest"])}']
    if drift:
        lines.append(f'<b>changed since ingest</b> &mdash; recorded '
                     f'{_e(record["digest"][:16])}&hellip;, re-ingest to record this version')
    body = "<br>".join(lines)
    return (f'<p class="prov{" drift" if drift else ""}">{body}</p>'
            f"{_history(versions, record.get('version_id'))}")


def _history(versions: list[dict[str, Any]], current: str | None) -> str:
    """Every version this asset holds, oldest first.

    One version is not a history worth a table; the provenance line above already
    names it. Two or more is the thing a reader came here for.
    """
    if len(versions) < 2:
        return ""
    rows = "".join(
        f'<tr><td>{position + 1}</td><td>{_e(entry["role"])}</td>'
        f'<td><code>{_e(entry["digest"][:12])}</code></td>'
        f'<td>{entry["size"]:,}</td>'
        f'<td>{"current" if entry["version_id"] == current else ""}</td></tr>'
        for position, entry in enumerate(versions))
    return ('<details class="hist"><summary>'
            f'{len(versions)} versions held</summary>'
            '<div class="scroll"><table><thead><tr><th>#</th><th>Role</th><th>Digest</th>'
            f'<th>Bytes</th><th></th></tr></thead><tbody>{rows}</tbody></table></div>'
            "</details>")


def _outline(document: dict[str, Any]) -> str:
    """The document's own headings. Skipped when there is nothing to navigate."""
    entries = document.get("outline") or []
    if len(entries) < 3:
        return ""
    links = "".join(
        f'<a class="d{entry["level"]}" href="#{_e(entry["anchor"])}">{_e(entry["text"])}</a>'
        for entry in entries)
    return f'<nav class="outline"><b>On this page</b>{links}</nav>'


def _citations(document: dict[str, Any], titles: dict[str, str]) -> str:
    """Which documents this one cites, and which cite it. Derived, never asserted."""
    blocks = []
    for label, key in (("Cites", "cites"), ("Cited by", "cited_by")):
        names = [identifier for identifier in document.get(key, []) if identifier in titles]
        if not names:
            continue
        links = "".join(f'<a href="#{_e(name)}">{_e(titles[name])}</a>' for name in names)
        blocks.append(f'<div class="cites"><span class="l">{label}</span>{links}</div>')
    return "".join(blocks)


def _article(document: dict[str, Any], titles: dict[str, str]) -> str:
    return (f'<article id="doc-{_e(document["id"])}">'
            f'<p class="crumb">{_e(document["path"])}</p>'
            f'<h1>{_e(document["title"])}</h1>'
            f'{_facet_tags(document)}{_provenance(document)}{_outline(document)}'
            f'{document["html"]}{_citations(document, titles)}</article>')


def _nav(groups: list[tuple[str, list[dict[str, Any]]]], order: dict[str, int]) -> str:
    """One section per kind, each link carrying every facet a filter can match on."""
    sections = []
    for label, documents in groups:
        links = "".join(
            f'<a href="#{_e(d["id"])}" data-id="{_e(d["id"])}" data-n="{order[d["id"]]}" '
            f'data-kind="{_e(d["facets"]["kind"])}" '
            f'data-settled="{_e(d["facets"]["settled"])}" '
            f'data-boundary="{_e(d["facets"]["boundary"])}">{_e(d["title"])}</a>'
            for d in documents)
        sections.append(
            f'<section data-kind="{_e(label)}"><b>{_e(label)} '
            f'<span>{len(documents)}</span></b>{links}</section>')
    return "".join(sections)


def _facet_bar(documents: list[dict[str, Any]], facet: str, label: str) -> str:
    """Filter chips for one facet, each showing how many documents carry it."""
    counts: dict[str, int] = {}
    for document in documents:
        value = document["facets"].get(facet)
        if value:
            counts[value] = counts.get(value, 0) + 1
    if len(counts) < 2:
        return ""
    chips = "".join(
        f'<button data-facet="{_e(facet)}" data-value="{_e(value)}" aria-pressed="false">'
        f'{_e(value)} <span>{count}</span></button>'
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])))
    return f'<div class="grp" data-label="{_e(label)}">{chips}</div>'


def _facet_tags(document: dict[str, Any]) -> str:
    """The document's own facets, shown where a reader meets the document."""
    facets = document["facets"]
    shown = [("kind", facets["kind"]), ("standing", facets["standing"]),
             ("boundary", facets["boundary"])]
    if facets.get("office"):
        shown.append(("office", facets["office"]))
    if facets.get("village"):
        shown.append(("village", facets["village"]))
    tags = "".join(f'<span class="ft"><i>{_e(name)}</i>{_e(value)}</span>'
                   for name, value in shown)
    note = facets.get("kind_note") or ""
    return f'<div class="facets">{tags}</div>' + (
        f'<p class="kindnote">{_e(note)}</p>' if note else "")


def render(documents: list[dict[str, Any]], groups: list[tuple[str, list[dict[str, Any]]]],
           ingested: int) -> str:
    """Build the whole site. Same documents in, same bytes out."""
    order = {document["id"]: position for position, document in enumerate(documents)}
    titles = {document["id"]: document["title"] for document in documents}
    index = [{"id": d["id"], "p": d["path"].lower(), "t": d["search"]} for d in documents]
    payload = json.dumps(index, separators=(",", ":"), sort_keys=True)
    citations = sum(len(document.get("cites", [])) for document in documents)
    bars = (_facet_bar(documents, "settled", "standing")
            + _facet_bar(documents, "boundary", "boundary"))
    return (
        "<title>Soveraeign Documentation</title>"
        f"<style>{STYLE}</style>"
        '<button id="focus" type="button">focus</button>'
        '<nav id="nav"><h1>Soveraeign</h1>'
        f'<span class="count">{len(documents)} documents &middot; {ingested} ingested '
        f'&middot; {citations} citations</span>'
        '<input id="q" type="search" placeholder="Filter by title or text" '
        'autocomplete="off" spellcheck="false">'
        f'{bars}'
        f'{_nav(groups, order)}'
        '<p id="empty" style="font-size:.8rem;padding:.4rem">Nothing matches.</p></nav>'
        f'<main>{"".join(_article(document, titles) for document in documents)}</main>'
        f"<script>window.__DOCS__={payload};</script>"
        f"<script>{SCRIPT}</script>")
