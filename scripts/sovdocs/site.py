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


STYLE = """
:root {
  --bg:#fbfbf9; --fg:#1a1a18; --muted:#6b6b64; --line:#e2e0d8; --card:#fff;
  --accent:#2f5d50; --warn:#8a4b1f; --code:#f4f3ee; --nav:#f7f6f1;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg:#15151a; --fg:#e9e9e5; --muted:#9a9a93; --line:#2c2c33; --card:#1c1c21;
    --accent:#7fc0ac; --warn:#d69a63; --code:#202027; --nav:#1a1a20;
  }
}
* { box-sizing:border-box; }
html,body { height:100%; }
body { margin:0; background:var(--bg); color:var(--fg); display:flex;
  font:15px/1.65 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }
#nav { width:19rem; flex:0 0 19rem; height:100vh; overflow-y:auto; background:var(--nav);
  border-right:1px solid var(--line); padding:1rem .75rem 3rem; position:sticky; top:0; }
#nav h1 { font-size:.95rem; margin:.2rem .4rem .1rem; letter-spacing:-.01em; }
#nav .count { font-size:.75rem; color:var(--muted); margin:0 .4rem .75rem; display:block; }
#q { width:100%; padding:.45rem .6rem; border:1px solid var(--line); border-radius:.4rem;
  background:var(--card); color:var(--fg); font:inherit; font-size:.85rem; margin-bottom:.75rem; }
#nav section { margin-bottom:.5rem; }
#nav section > b { display:block; font-size:.72rem; text-transform:uppercase;
  letter-spacing:.06em; color:var(--muted); padding:.4rem .4rem .2rem; }
#nav a { display:block; padding:.22rem .45rem; border-radius:.3rem; color:var(--fg);
  text-decoration:none; font-size:.83rem; }
#nav a:hover { background:var(--card); }
#nav a.on { background:var(--accent); color:var(--bg); }
#nav a.hide { display:none; }
main { flex:1; min-width:0; height:100vh; overflow-y:auto; padding:2.5rem 3rem 6rem; }
article { max-width:48rem; display:none; }
article.on { display:block; }
.crumb { font-size:.78rem; color:var(--muted); margin-bottom:.2rem;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }
.prov { font-size:.74rem; color:var(--muted); border:1px solid var(--line); background:var(--card);
  border-radius:.4rem; padding:.5rem .7rem; margin:0 0 2rem;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace; overflow-x:auto; }
.prov.drift { border-color:var(--warn); color:var(--warn); }
article h1 { font-size:1.55rem; margin:.2rem 0 1rem; letter-spacing:-.015em; }
article h2 { font-size:1.2rem; margin:2rem 0 .6rem; padding-bottom:.25rem;
  border-bottom:1px solid var(--line); }
article h3 { font-size:1.02rem; margin:1.5rem 0 .4rem; }
article h4,article h5,article h6 { font-size:.92rem; margin:1.2rem 0 .3rem; color:var(--muted); }
article p { margin:0 0 .9rem; }
article ul,article ol { margin:0 0 .9rem; padding-left:1.35rem; }
article li { margin-bottom:.2rem; }
article li > ul, article li > ol { margin:.2rem 0 .3rem; }
article a { color:var(--accent); }
article code { background:var(--code); border:1px solid var(--line); border-radius:.25rem;
  padding:.04rem .28rem; font:12.5px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace; }
article pre { background:var(--code); border:1px solid var(--line); border-radius:.45rem;
  padding:.75rem .9rem; overflow-x:auto; margin:0 0 1rem; }
article pre code { background:none; border:0; padding:0; font-size:12.5px; line-height:1.55; }
article blockquote { margin:0 0 1rem; padding:.1rem 0 .1rem .9rem;
  border-left:3px solid var(--line); color:var(--muted); }
article hr { border:0; border-top:1px solid var(--line); margin:1.8rem 0; }
.scroll { overflow-x:auto; margin:0 0 1.1rem; }
table { border-collapse:collapse; font-size:.86rem; width:100%; }
th,td { border:1px solid var(--line); padding:.35rem .6rem; text-align:left; vertical-align:top; }
th { background:var(--card); font-weight:600; }
#empty { color:var(--muted); display:none; }
#empty.on { display:block; }
@media (max-width:800px) {
  body { flex-direction:column; }
  #nav { width:auto; flex:none; height:auto; position:static; border-right:0;
    border-bottom:1px solid var(--line); max-height:16rem; }
  main { height:auto; padding:1.5rem 1.1rem 4rem; }
}
"""

SCRIPT = """
(function () {
  var index = window.__DOCS__ || [];
  var links = Array.prototype.slice.call(document.querySelectorAll('#nav a'));
  var box = document.getElementById('q');
  var empty = document.getElementById('empty');

  function show(id) {
    document.querySelectorAll('article').forEach(function (a) {
      a.classList.toggle('on', a.id === 'doc-' + id);
    });
    links.forEach(function (a) { a.classList.toggle('on', a.dataset.id === id); });
    document.querySelector('main').scrollTop = 0;
    try { history.replaceState(null, '', '#' + id); } catch (e) { /* file:// */ }
  }

  links.forEach(function (a) {
    a.addEventListener('click', function (e) { e.preventDefault(); show(a.dataset.id); });
  });

  box.addEventListener('input', function () {
    var q = box.value.trim().toLowerCase();
    var hits = 0;
    links.forEach(function (a) {
      var entry = index[Number(a.dataset.n)];
      var match = !q || entry.p.indexOf(q) !== -1 || entry.t.indexOf(q) !== -1;
      a.classList.toggle('hide', !match);
      if (match) { hits++; }
    });
    empty.classList.toggle('on', hits === 0);
    document.querySelectorAll('#nav section').forEach(function (s) {
      var any = Array.prototype.some.call(s.querySelectorAll('a'), function (a) {
        return !a.classList.contains('hide');
      });
      s.style.display = any ? '' : 'none';
    });
  });

  var start = (location.hash || '').replace(/^#/, '');
  show(index.some(function (e) { return e.id === start; }) ? start : index[0].id);
})();
"""


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _provenance(document: dict[str, Any]) -> str:
    record = document.get("asset")
    if not record:
        return ('<p class="prov">Not yet ingested. Run '
                '<code>python scripts/sov_docs.py ingest</code> to give this document '
                'an addressed source and a receipt.</p>')
    drift = record["digest"] != document["digest"]
    body = (f'asset {_e(record["asset_id"])} &middot; version {_e(record["version_id"])}'
            f'<br>receipt {_e(record["receipt_id"])}'
            f'<br>digest {_e(document["digest"])}')
    if drift:
        body += (f'<br><b>changed since ingest</b> &mdash; recorded '
                 f'{_e(record["digest"][:16])}&hellip;, re-ingest to record this version')
    return f'<p class="prov{" drift" if drift else ""}">{body}</p>'


def _article(document: dict[str, Any]) -> str:
    return (f'<article id="doc-{_e(document["id"])}">'
            f'<p class="crumb">{_e(document["path"])}</p>'
            f'<h1>{_e(document["title"])}</h1>'
            f'{_provenance(document)}{document["html"]}</article>')


def _nav(groups: list[tuple[str, list[dict[str, Any]]]], order: dict[str, int]) -> str:
    sections = []
    for label, documents in groups:
        links = "".join(
            f'<a href="#{_e(d["id"])}" data-id="{_e(d["id"])}" data-n="{order[d["id"]]}">'
            f'{_e(d["title"])}</a>'
            for d in documents)
        sections.append(f"<section><b>{_e(label)}</b>{links}</section>")
    return "".join(sections)


def render(documents: list[dict[str, Any]], groups: list[tuple[str, list[dict[str, Any]]]],
           ingested: int) -> str:
    """Build the whole site. Same documents in, same bytes out."""
    order = {document["id"]: position for position, document in enumerate(documents)}
    index = [{"id": d["id"], "p": d["path"].lower(), "t": d["search"]} for d in documents]
    payload = json.dumps(index, separators=(",", ":"), sort_keys=True)
    return (
        "<title>Soveraeign Documentation</title>"
        f"<style>{STYLE}</style>"
        '<nav id="nav"><h1>Soveraeign</h1>'
        f'<span class="count">{len(documents)} documents &middot; {ingested} ingested</span>'
        '<input id="q" type="search" placeholder="Filter by title or text" '
        'autocomplete="off" spellcheck="false">'
        f'{_nav(groups, order)}'
        '<p id="empty" style="font-size:.8rem;padding:.4rem">Nothing matches.</p></nav>'
        f'<main>{"".join(_article(document) for document in documents)}</main>'
        f"<script>window.__DOCS__={payload};</script>"
        f"<script>{SCRIPT}</script>")
