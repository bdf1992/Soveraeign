"""Discord-like composable shell over canonical Human Binding records.

Adds navigation, query, card, and utility composition but no state, route, authority, or standing.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from sovsurface.cards import operation_card, service_card, subject_card
from sovsurface.primitives import badge, e, empty_state, metric, nav_item, panel, rail_item


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
background:var(--card);border-radius:8px}.browse-card{padding:12px;min-height:124px}.browse-card h3{font-size:14px;margin:3px 0 7px}
.browse-card p{margin:7px 0}.card-statline{color:var(--muted);font-size:12px}.text-action{border:0;background:none;
color:#9da4ff;padding:4px 0;cursor:pointer;font-weight:650}.badges{display:flex;gap:4px;flex-wrap:wrap}.badge{font-size:9px;
letter-spacing:.04em;text-transform:uppercase;border:1px solid var(--line);border-radius:4px;padding:2px 5px;color:var(--muted)}
.badge.positive{color:var(--positive);border-color:#40715f}.badge.warning{color:var(--warning);border-color:#805939}
.op{margin:7px 0;overflow:hidden}.op>summary{list-style:none;display:flex;align-items:center;gap:10px;padding:10px 12px;
cursor:pointer}.op>summary::-webkit-details-marker{display:none}.op[open]>summary{background:#2a2c31}.card-leading{display:flex;
flex-direction:column;gap:2px;min-width:0;margin-right:auto}.op code.id{font-weight:750;color:var(--fg);background:none;border:0;padding:0}
.operation-subject{font-size:11px;color:var(--muted)}.op-body{border-top:1px solid var(--line);padding:12px}
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

SCRIPT = r"""
(() => {
  const input = document.querySelector('[data-query]');
  const count = document.querySelector('[data-result-count]');
  const cards = [...document.querySelectorAll('[data-card]')];
  const filters = new Set(['service','affordance','subject','authority','kind']);
  const normalize = value => (value || '').toLowerCase().trim();
  function matches(card, query) {
    const tokens = query.match(/(?:"[^"]*"|\S+)/g) || [];
    const haystack = normalize(card.dataset.search);
    return tokens.every(raw => {
      const token = raw.replace(/^"|"$/g,'');
      const split = token.indexOf(':');
      if (split > 0) {
        const key = normalize(token.slice(0, split));
        const value = normalize(token.slice(split + 1));
        if (filters.has(key)) return normalize(card.dataset[key]) === value;
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


def _service_map(interface: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    services: dict[str, list[dict[str, Any]]] = {}
    for operation in interface["operations"]:
        services.setdefault(operation["service_id"], []).append(operation)
    return services


def _rail(services: dict[str, list[dict[str, Any]]]) -> str:
    items = [rail_item("Node home", short="S", active=True)]
    items.append('<div class="rail-sep"></div>')
    for service in sorted(services):
        items.append(
            rail_item(
                f"{service} service",
                short=service,
                filter_value=f"service:{service}",
            )
        )
    return f'<aside class="rail" data-component="service-rail">{"".join(items)}</aside>'


def _nav(interface: dict[str, Any], services: dict[str, list[dict[str, Any]]]) -> str:
    counts = Counter(item["affordance"]["kind"] for item in interface["operations"])
    rows = [
        nav_item("Everything", icon="⌂", active=True, count=len(interface["operations"])),
        nav_item("Actions", icon="▶", count=counts["ACTION"], filter_value="affordance:ACTION"),
        nav_item("Reads", icon="↳", count=counts["READ"], filter_value="affordance:READ"),
        nav_item("Inspect", icon="◇", count=counts["INSPECT"], filter_value="affordance:INSPECT"),
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
        + '<div class="section-label">Assets & subjects</div>'
        + nav_item("Asset service", icon="▣", filter_value="service:asset")
        + nav_item("Declared subjects", icon="◆", filter_value="kind:subject")
        + "</aside>"
    )


def _utility(interface: dict[str, Any]) -> str:
    counts = Counter(item["affordance"]["kind"] for item in interface["operations"])
    exposure = "".join(
        f'<div class="utility-row"><span>{e(kind)}</span><b>{count}</b></div>'
        for kind, count in sorted(counts.items())
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
        "<code>kind:operation</code></div>"
    )
    live = panel(
        "No live presence implied",
        '<p class="muted">Operators, sessions, object instances, and harness state appear only '
        "when a governed read source projects them. This shell does not fake an Active Now list.</p>",
        eyebrow="presence",
    )
    return (
        '<aside class="utility" data-component="utility-drawer">'
        "<h2>What this node exposes</h2>"
        f'<div class="panel"><div class="utility-list">{exposure}</div></div>'
        "<h2>Query grammar</h2>"
        + panel("Filter the same records", help_body, eyebrow="search")
        + "<h2>Presence</h2>"
        + live
        + "<h2>Material omissions</h2>"
        + omissions
        + "</aside>"
    )


def _main(interface: dict[str, Any], services: dict[str, list[dict[str, Any]]]) -> str:
    counts = interface["counts"]
    subjects: dict[str, list[dict[str, Any]]] = {}
    for operation in interface["operations"]:
        subjects.setdefault(operation["subject"], []).append(operation)
    hero = (
        '<div class="hero"><div class="hero-copy"><div class="eyebrow">human binding · composed view</div>'
        "<h2>One Node, browsable like a workspace.</h2>"
        '<p>Discord-like navigation is used as interaction grammar: rail, browser, feed, utility drawer, '
        "cards, and query filters. Every card is still derived from the same operation record; layout "
        "cannot manufacture reachability, authority, standing, live presence, or object instances.</p></div>"
        '<div class="metrics">'
        + metric(counts["declared"], "declared operations")
        + metric(counts["reachable"], "exact routes")
        + metric(counts["policy_active"], "policy-active")
        + metric(counts["observed"], "admitted observations")
        + "</div></div>"
    )
    toolbar = (
        '<div class="toolbar" data-component="filter-pills">'
        '<button class="pill active" data-filter="" type="button">All cards</button>'
        '<button class="pill" data-filter="kind:service" type="button">Services</button>'
        '<button class="pill" data-filter="kind:subject" type="button">Subjects</button>'
        '<button class="pill" data-filter="kind:operation" type="button">Operations</button>'
        '<button class="pill" data-filter="service:asset" type="button">Asset browser</button>'
        '<button class="pill" data-filter="affordance:ACTION" type="button">Callable actions</button>'
        "</div>"
    )
    service_cards = "".join(service_card(service, ops) for service, ops in sorted(services.items()))
    subject_cards = "".join(subject_card(subject, ops) for subject, ops in sorted(subjects.items()))
    operation_cards = "".join(operation_card(item) for item in interface["operations"])
    return (
        '<main class="main" data-component="workspace">'
        + hero
        + toolbar
        + '<section class="surface-section"><header><h2>Services</h2>'
        '<p>Discord server/channel density, mapped onto actual service boundaries.</p></header>'
        f'<div class="card-grid">{service_cards}</div></section>'
        '<section class="surface-section"><header><h2>Asset & subject browser</h2>'
        '<p>Declared subjects only; object instances remain an explicit omission.</p></header>'
        f'<div class="card-grid">{subject_cards}</div></section>'
        '<section class="surface-section"><header><h2>Operations</h2>'
        '<p>Expand a card to inspect exact authority, route, refusal, source, and digest facts.</p></header>'
        f'<div>{operation_cards}</div></section>'
        '<div data-no-results hidden>'
        + empty_state("No cards match", "Change the query or clear filters.")
        + "</div></main>"
    )


def render(interface: dict[str, Any]) -> str:
    """Render an alternate composable shell over the exact canonical interface."""
    services = _service_map(interface)
    node = interface["node"]
    top = (
        '<header class="topbar" data-component="command-bar">'
        f'<h1>{e(node["display_name"])}</h1><span class="badge muted">projection only</span>'
        '<div class="search"><input data-query aria-label="Filter Node cards" '
        'placeholder="Search or filter: service:asset affordance:ACTION"><kbd>Ctrl K</kbd></div>'
        '<span class="result-count" data-result-count></span></header>'
    )
    status = (
        '<footer class="status">NODE INTERFACE · '
        f'{e(interface["input_state_digest"])} · rendering grants nothing · not an observation</footer>'
    )
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Soveraeign Composable Human Surface</title>"
        f"<style>{STYLE}</style></head><body><div class=\"shell\">"
        + _rail(services)
        + _nav(interface, services)
        + top
        + _main(interface, services)
        + _utility(interface)
        + status
        + f"</div><script>{SCRIPT}</script></body></html>"
    )
