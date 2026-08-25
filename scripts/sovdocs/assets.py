"""How the documentation page looks and behaves in a browser.

Held apart from `site.py` so that module assembles the page and this one
carries its presentation. Both are inlined at build time: the page must open
from a file URL with no stylesheet, script, or font fetched from anywhere.
"""

from __future__ import annotations


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
#nav .grp { display:flex; gap:.25rem; flex-wrap:wrap; margin:0 .35rem .55rem; }
#nav .grp::before { content:attr(data-label); width:100%; font-size:.66rem;
  text-transform:uppercase; letter-spacing:.07em; color:var(--muted); margin-bottom:.1rem; }
#nav .grp button span { opacity:.6; font-size:.64rem; }
#nav section > b span { opacity:.5; font-weight:400; }
.facets { display:flex; flex-wrap:wrap; gap:.3rem; margin:0 0 .5rem; }
.ft { font-size:.72rem; border:1px solid var(--line); border-radius:.25rem;
  padding:.08rem .4rem; color:var(--fg); background:var(--card); }
.ft i { font-style:normal; color:var(--muted); margin-right:.35rem;
  text-transform:uppercase; letter-spacing:.05em; font-size:.62rem; }
.kindnote { font-size:.78rem; color:var(--muted); margin:0 0 1.2rem; }
#nav .grp button { font:inherit; font-size:.7rem; padding:.15rem .4rem; border-radius:.25rem;
  border:1px solid var(--line); background:var(--card); color:var(--muted); cursor:pointer; }
#nav .grp button[aria-pressed="true"] { background:var(--accent); color:var(--bg);
  border-color:var(--accent); }
a.cite { text-decoration:none; }
a.cite code { border-style:dashed; }
a.cite:hover code { border-color:var(--accent); color:var(--accent); }
.unresolved { border-bottom:1px dotted var(--muted); color:var(--muted); }
.outline { border:1px solid var(--line); background:var(--card); border-radius:.45rem;
  padding:.6rem .8rem; margin:0 0 1.6rem; font-size:.84rem; }
.outline b { display:block; font-size:.7rem; text-transform:uppercase; letter-spacing:.06em;
  color:var(--muted); margin-bottom:.3rem; }
.outline a { display:block; color:var(--fg); text-decoration:none; padding:.08rem 0; }
.outline a:hover { color:var(--accent); }
.outline a.d3 { padding-left:1rem; color:var(--muted); font-size:.8rem; }
.cites { display:flex; flex-wrap:wrap; gap:.3rem; margin:0 0 1.2rem; }
.cites span.l { font-size:.72rem; text-transform:uppercase; letter-spacing:.06em;
  color:var(--muted); width:100%; }
.cites a { font-size:.78rem; padding:.1rem .4rem; border:1px solid var(--line);
  border-radius:.25rem; color:var(--fg); text-decoration:none; background:var(--card); }
.cites a:hover { border-color:var(--accent); color:var(--accent); }
.hist { margin:-1.4rem 0 1.8rem; font-size:.8rem; }
.hist > summary { cursor:pointer; color:var(--muted); font-size:.76rem; }
.hist table { margin-top:.4rem; font-size:.78rem; }
body.focus #nav { display:none; }
body.focus main { padding-left:max(3rem, calc(50vw - 26rem)); }
#focus { position:fixed; top:.6rem; right:.9rem; z-index:5; font:inherit; font-size:.72rem;
  padding:.2rem .5rem; border:1px solid var(--line); border-radius:.25rem;
  background:var(--card); color:var(--muted); cursor:pointer; }
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
  var ids = {};
  index.forEach(function (e) { ids[e.id] = true; });
  var links = Array.prototype.slice.call(document.querySelectorAll('#nav a'));
  var box = document.getElementById('q');
  var empty = document.getElementById('empty');
  var group = null;

  function show(id, anchor) {
    document.querySelectorAll('article').forEach(function (a) {
      a.classList.toggle('on', a.id === 'doc-' + id);
    });
    links.forEach(function (a) { a.classList.toggle('on', a.dataset.id === id); });
    var main = document.querySelector('main');
    main.scrollTop = 0;
    if (anchor) {
      var target = document.getElementById('doc-' + id);
      var heading = target && target.querySelector('[id="' + anchor + '"]');
      if (heading) { heading.scrollIntoView({ block: 'start' }); }
    }
    try { history.replaceState(null, '', '#' + id); } catch (e) { /* file:// */ }
  }

  links.forEach(function (a) {
    a.addEventListener('click', function (e) { e.preventDefault(); show(a.dataset.id); });
  });

  // A citation inside a document points at another document by id. Without this
  // the browser would move the fragment and leave the hidden article hidden.
  document.querySelector('main').addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a) { return; }
    var target = a.getAttribute('href').slice(1);
    if (ids[target]) { e.preventDefault(); show(target); return; }
    var current = document.querySelector('article.on');
    var heading = current && current.querySelector('[id="' + target + '"]');
    if (heading) { e.preventDefault(); heading.scrollIntoView({ block: 'start' }); }
  });

  var chosen = {};

  function apply() {
    var q = box.value.trim().toLowerCase();
    var hits = 0;
    links.forEach(function (a) {
      var entry = index[Number(a.dataset.n)];
      var text = !q || entry.p.indexOf(q) !== -1 || entry.t.indexOf(q) !== -1;
      // Facets compose: a document must satisfy every facet that has a choice.
      var faceted = Object.keys(chosen).every(function (facet) {
        return a.dataset[facet] === chosen[facet];
      });
      var match = text && faceted;
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
  }

  box.addEventListener('input', apply);

  document.querySelectorAll('#nav .grp button').forEach(function (b) {
    b.addEventListener('click', function () {
      var facet = b.dataset.facet;
      var value = b.dataset.value;
      if (chosen[facet] === value) { delete chosen[facet]; } else { chosen[facet] = value; }
      document.querySelectorAll('#nav .grp button').forEach(function (other) {
        other.setAttribute('aria-pressed',
          String(chosen[other.dataset.facet] === other.dataset.value));
      });
      apply();
    });
  });

  var focus = document.getElementById('focus');
  focus.addEventListener('click', function () {
    var on = document.body.classList.toggle('focus');
    focus.textContent = on ? 'show list' : 'focus';
  });

  var start = (location.hash || '').replace(/^#/, '');
  show(ids[start] ? start : index[0].id);
})();
"""
