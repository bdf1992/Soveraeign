"""Presentation constants for the composed Human Binding shell.

The query script is deliberately data-driven: it reads the filterable keys each
collection declared from a JSON manifest in the page, so adding a facet is a
change to a record adapter and never a change to this script.

Nothing here reads, writes, fetches, or navigates. Filtering changes visibility;
expanding a card changes presentation. Neither touches a source.
"""

from __future__ import annotations

STYLE = r"""
:root{--bg:#111214;--rail:#0b0c0e;--nav:#17181b;--main:#1d1f22;--utility:#17181b;
--card:#24262a;--card2:#202226;--line:#303238;--fg:#f2f3f5;--muted:#a3a6ad;--quiet:#747982;
--accent:#7c86ff;--positive:#6fcba6;--warning:#e1a36e;--danger:#ed7c83;--shadow:0 8px 24px #0004}
*{box-sizing:border-box}html,body{height:100%}body{margin:0;background:var(--bg);color:var(--fg);
font:14px/1.45 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;overflow:hidden}
button,input{font:inherit}button{color:inherit}.shell{display:grid;height:100vh;
grid-template-columns:72px 246px minmax(420px,1fr) 292px;grid-template-rows:48px 1fr 28px;
grid-template-areas:"rail nav top utility" "rail nav main utility" "rail nav status utility"}
.topbar{grid-area:top;display:flex;align-items:center;gap:10px;padding:8px 14px;background:var(--main);
border-bottom:1px solid var(--line);min-width:0}.topbar h1{font-size:14px;margin:0;white-space:nowrap}
.search{margin-left:auto;max-width:560px;flex:1;position:relative}.search input{width:100%;border:1px solid #0000;
background:#101114;color:var(--fg);border-radius:6px;padding:7px 34px 7px 10px;outline:none}
.search input:focus{border-color:var(--accent)}.search kbd{position:absolute;right:8px;top:6px;
font-size:10px;color:var(--quiet);border:1px solid var(--line);padding:1px 4px;border-radius:3px}
.result-count{font-size:11px;color:var(--muted);white-space:nowrap}.rail{grid-area:rail;background:var(--rail);
border-right:1px solid #000;padding:10px 8px;display:flex;flex-direction:column;align-items:center;gap:8px;
overflow:auto}.rail-item{width:44px;height:44px;border:0;border-radius:14px;background:#282a2e;color:#c9cbd0;
font-weight:750;cursor:pointer;transition:.12s}.rail-item:hover,.rail-item.active{background:var(--accent);
color:white;border-radius:12px}.rail-sep{width:30px;height:1px;background:var(--line);margin:2px 0}
.nav{grid-area:nav;background:var(--nav);border-right:1px solid #111;padding:10px 8px;overflow:auto}
.node-name{padding:4px 8px 12px;border-bottom:1px solid var(--line);margin-bottom:9px}.node-name b{display:block}
.node-name span{color:var(--muted);font-size:11px}.section-label{font-size:10px;text-transform:uppercase;
letter-spacing:.09em;color:var(--quiet);font-weight:700;margin:15px 8px 6px}.nav-item{width:100%;display:flex;
align-items:center;gap:8px;border:0;background:transparent;color:var(--muted);padding:7px 8px;border-radius:5px;
text-align:left;cursor:pointer}.nav-item:hover,.nav-item.active{background:#2b2d31;color:var(--fg)}.nav-icon{width:16px;
color:var(--quiet)}.nav-item .count{margin-left:auto;font-size:11px;color:var(--quiet)}.main{grid-area:main;
background:var(--main);overflow:auto;padding:18px}.hero{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(260px,.8fr);
gap:12px;margin-bottom:16px}.hero-copy{background:linear-gradient(135deg,#292c35,#22242a);border:1px solid var(--line);
border-radius:10px;padding:18px}.hero-copy h2{font-size:23px;margin:4px 0 7px;letter-spacing:-.025em}.hero-copy p{color:var(--muted);
max-width:58rem;margin:0}.eyebrow{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:var(--quiet);
font-weight:750}.metrics{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.metric{background:var(--card);
border:1px solid var(--line);border-radius:8px;padding:11px}.metric b{display:block;font-size:20px}.metric span{color:var(--muted);
font-size:11px}.metric small{display:block;color:var(--quiet);font-size:10px;margin-top:2px}.toolbar{display:flex;gap:6px;
align-items:center;flex-wrap:wrap;margin:0 0 14px}.pill{border:1px solid var(--line);background:var(--card2);color:var(--muted);
padding:5px 9px;border-radius:999px;cursor:pointer;font-size:11px}.pill:hover,.pill.active{border-color:#5a61b7;color:var(--fg);
background:#303349}.surface-section{margin:22px 0}.surface-section>header{display:flex;align-items:end;gap:8px;margin-bottom:8px}
.surface-section h2{font-size:15px;margin:0}.surface-section header p{font-size:11px;color:var(--muted);margin:0}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:9px}.card{border:1px solid var(--line);
background:var(--card);border-radius:8px}
.card-statline{color:var(--muted);font-size:12px}.text-action{border:0;background:none;
color:#9da4ff;padding:4px 0;cursor:pointer;font-weight:650}.badges{display:flex;gap:4px;flex-wrap:wrap}.badge{font-size:9px;
letter-spacing:.04em;text-transform:uppercase;border:1px solid var(--line);border-radius:4px;padding:2px 5px;color:var(--muted)}
.badge.positive{color:var(--positive);border-color:#40715f}.badge.warning{color:var(--warning);border-color:#805939}
.card-leading{display:flex;
flex-direction:column;gap:2px;min-width:0;margin-right:auto}

.facts{display:grid;grid-template-columns:132px minmax(0,1fr);gap:7px 10px;margin:0}.facts dt{color:var(--quiet);
font-size:11px}.facts dd{margin:0;min-width:0;overflow-wrap:anywhere}.facts code,.source-row code{font:11px/1.4 ui-monospace,
SFMono-Regular,Menlo,monospace;background:#17181b;border:1px solid var(--line);padding:1px 4px;border-radius:4px}
.command{white-space:pre-wrap;background:#141518;border:1px solid var(--line);padding:8px;border-radius:6px;color:#d9dbdf}
.boundary{font-size:11px;color:var(--warning)}.source-list{max-height:120px;overflow:auto}.source-row{display:grid;
grid-template-columns:94px minmax(0,1fr);gap:7px;margin:3px 0;color:var(--muted);font-size:11px}.utility{grid-area:utility;
background:var(--utility);border-left:1px solid #111;padding:12px;overflow:auto}.utility h2{font-size:11px;text-transform:uppercase;
letter-spacing:.08em;color:var(--quiet);margin:12px 4px 7px}.panel{background:var(--card2);border:1px solid var(--line);
border-radius:8px;padding:10px;margin:7px 0}.panel h3{font-size:12px;margin:2px 0 7px}.panel p{margin:5px 0}.muted{color:var(--muted)}
.utility-list{display:grid;gap:5px}.utility-row{display:flex;justify-content:space-between;gap:10px;color:var(--muted);
font-size:11px}.utility-row b{color:var(--fg)}.query-help code{display:block;margin:4px 0;color:#b9beff;font-size:10px}
.empty-state{text-align:center;padding:22px;border:1px dashed var(--line);border-radius:8px;color:var(--muted)}
.empty-state strong{color:var(--fg)}.status{grid-area:status;border-top:1px solid var(--line);background:#151619;color:var(--quiet);
font:10px/27px ui-monospace,SFMono-Regular,Menlo,monospace;padding:0 10px;white-space:nowrap;overflow:hidden}
[data-card][hidden]{display:none!important}.omission{border-left:3px solid var(--warning)}
@media(max-width:1120px){.shell{grid-template-columns:64px 220px 1fr;grid-template-areas:"rail nav top" "rail nav main" "rail nav status"}
.utility{display:none}}@media(max-width:760px){body{overflow:auto}.shell{display:block;height:auto}.rail{display:none}.nav{display:none}
.topbar{position:sticky;top:0;z-index:5}.main{min-height:100vh}.status{display:none}.hero{grid-template-columns:1fr}.facts{grid-template-columns:1fr}}
"""

EXTRA = r"""
.card-rows{display:grid;gap:6px}.grid-card,.row-card{padding:0}.card>summary{list-style:none;display:flex;
align-items:center;gap:10px;padding:10px 12px;cursor:pointer;min-height:52px}
.card>summary::-webkit-details-marker{display:none}.card[open]>summary{background:#2a2c31}
.card-title{font-weight:750;overflow-wrap:anywhere}.card-body{border-top:1px solid var(--line);padding:12px}
.card-body>.card-statline,.card-body>p{margin:0 0 8px}.inspector{display:grid;gap:10px}
.inspector-section{border-top:1px dashed var(--line);padding-top:8px}.inspector-section:first-child{border-top:0;padding-top:0}
.provenance{display:flex;align-items:center;gap:6px;color:var(--quiet);font-size:11px;margin:0 0 8px}
.omission-note{color:var(--warning);font-size:11px;margin:0 0 8px}
.affordance{display:flex;flex-direction:column;gap:2px;margin:5px 0}
[data-collection][hidden]{display:none!important}
"""

SCRIPT = r"""
(() => {
  const input = document.querySelector('[data-query]');
  const count = document.querySelector('[data-result-count]');
  const cards = [...document.querySelectorAll('[data-card]')];
  const manifest = document.querySelector('[data-facet-keys]');
  const filters = new Set(JSON.parse(manifest ? manifest.textContent : '[]'));
  const normalize = value => (value || '').toLowerCase().trim();
  function facetHit(card, key, value) {
    const raw = normalize(card.dataset[key]);
    if (!raw) return false;
    return raw.split(/\s+/).includes(value);
  }
  function matches(card, query) {
    const tokens = query.match(/(?:"[^"]*"|\S+)/g) || [];
    const haystack = normalize(card.dataset.search) + ' ' + normalize(card.dataset.identity);
    return tokens.every(raw => {
      const token = raw.replace(/^"|"$/g,'');
      const split = token.indexOf(':');
      if (split > 0) {
        const key = normalize(token.slice(0, split));
        const value = normalize(token.slice(split + 1));
        if (filters.has(key)) return facetHit(card, key, value);
      }
      return haystack.includes(normalize(token));
    });
  }
  function apply(query) {
    const value = query.trim();
    let shown = 0;
    cards.forEach(card => {
      card.hidden = value ? !matches(card, value) : false;
      if (!card.hidden) shown += 1;
    });
    document.querySelectorAll('[data-collection]').forEach(section => {
      const owned = [...section.querySelectorAll('[data-card]')];
      section.hidden = owned.length > 0 && owned.every(card => card.hidden);
    });
    const none = document.querySelector('[data-no-results]');
    if (none) none.hidden = shown > 0;
    if (count) count.textContent = `${shown} / ${cards.length} cards`;
    document.querySelectorAll('[data-filter]').forEach(button => {
      button.classList.toggle('active', button.dataset.filter === value);
    });
  }
  document.addEventListener('click', event => {
    const trigger = event.target.closest('[data-filter]');
    if (!trigger) return;
    input.value = trigger.dataset.filter || '';
    apply(input.value);
    input.focus();
  });
  input.addEventListener('input', () => apply(input.value));
  window.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault(); input.focus(); input.select();
    }
    if (event.key === 'Escape' && document.activeElement === input) {
      input.value = ''; apply('');
    }
  });
  apply('');
})();
"""
