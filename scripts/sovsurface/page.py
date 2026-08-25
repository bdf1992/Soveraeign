"""Render the canonical Node Interface as a deterministic offline human surface."""

from __future__ import annotations

from typing import Any
import html

from sovnode.affordances import INVOKABLE

STYLE = """
:root{--bg:#f7f6f2;--fg:#171916;--muted:#666a62;--line:#d9dbd3;--card:#fff;
--yes:#176a50;--warn:#98531e;--no:#8d9189;--ink:#253d35}
@media(prefers-color-scheme:dark){:root{--bg:#151719;--fg:#e9ebe7;--muted:#9da39a;
--line:#30352f;--card:#1c1f21;--yes:#78c9aa;--warn:#dfa06c;--no:#737970;--ink:#b9d8ca}}
*{box-sizing:border-box}body{margin:0;padding:2rem 1.2rem 5rem;background:var(--bg);color:var(--fg);
font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}main{max-width:70rem;margin:auto}
h1{font-size:1.75rem;margin:0 0 .25rem;letter-spacing:-.025em}h2{font-size:1.05rem;margin:2.5rem 0 .75rem;
padding-bottom:.35rem;border-bottom:1px solid var(--line)}.sub{color:var(--muted);margin:.15rem 0 1.4rem}
.identity{display:grid;grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));gap:.55rem;margin:0 0 1rem}
.identity div,.counts li{background:var(--card);border:1px solid var(--line);border-radius:.5rem;padding:.65rem .8rem}
.identity small,.counts span{display:block;color:var(--muted);font-size:.75rem}.identity code{font-size:.85rem}
.counts{display:flex;flex-wrap:wrap;gap:.45rem;list-style:none;padding:0;margin:0 0 1.2rem}.counts b{font-size:1.35rem}
.note{border-left:3px solid var(--warn);background:var(--card);padding:.75rem 1rem;margin:0 0 1.8rem;
border-radius:0 .4rem .4rem 0}.note b{color:var(--warn)}.note ul{margin:.35rem 0 0;padding-left:1.1rem}
.op{background:var(--card);border:1px solid var(--line);border-radius:.5rem;margin:.55rem 0;overflow:hidden}
.op>summary{cursor:pointer;padding:.62rem .8rem;display:flex;flex-wrap:wrap;align-items:center;gap:.45rem}
.op .id{font-weight:650;margin-right:auto}.body{border-top:1px solid var(--line);padding:.1rem .8rem .85rem}
.tag{font-size:.68rem;text-transform:uppercase;letter-spacing:.035em;padding:.1rem .35rem;border:1px solid var(--line);
border-radius:.25rem;color:var(--no);white-space:nowrap}.tag.yes{color:var(--yes);border-color:var(--yes)}
.tag.warn{color:var(--warn);border-color:var(--warn)}dl{display:grid;grid-template-columns:10rem 1fr;gap:.3rem .8rem}
dt{font-size:.8rem;color:var(--muted)}dd{margin:0;font-size:.88rem}code,pre{font:12.5px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}
code{background:var(--bg);border:1px solid var(--line);border-radius:.22rem;padding:.04rem .25rem}
pre{overflow:auto;background:var(--bg);border:1px solid var(--line);border-radius:.35rem;padding:.6rem .7rem}
.sources{max-height:8rem;overflow:auto}.sources div{font:11.5px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--muted)}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--muted);font-size:.8rem}
@media(max-width:620px){dl{grid-template-columns:1fr}dt{margin-top:.45rem}}
"""


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _tag(label: str, value: bool) -> str:
    return f'<span class="tag {"yes" if value else ""}">{_e(label)}</span>'


def _policy(record: dict[str, Any]) -> str:
    parts = []
    for endpoint in record["policy_endpoints"]:
        active = endpoint["activation"] == "ACTIVE"
        kind = "yes" if active else "warn" if endpoint["activation"].startswith("REFUSED") else ""
        parts.append(f'<span class="tag {kind}">{_e(endpoint["transport"])} '
                     f'{_e(endpoint["activation"].lower().replace("_", " "))}</span>')
    return " ".join(parts)


def _sources(record: dict[str, Any]) -> str:
    rows = "".join(f'<div>{source["digest"][:12]} &nbsp; {_e(source["address"])}</div>'
                   for source in record["sources"])
    return f'<div class="sources">{rows}</div>'


def _try(record: dict[str, Any]) -> str:
    if record["affordance"]["kind"] not in INVOKABLE:
        return ""
    route = next(route for route in record["reachability"] if route["policy_active"])
    arguments = " ".join(f"{name}=..." for name in route["required_arguments"])
    command = (f"python scripts/sov_surface.py try {record['operation_id']} {arguments} "
               "--binding HUMAN --actor YOUR_ACTOR --scope YOUR_SCOPE")
    return ("<dt>Invoke</dt><dd><pre>" + _e(command) +
            "</pre>Requires authority already recorded for that actor and scope. "
            "The surface creates none.</dd>")


def _operation(record: dict[str, Any]) -> str:
    facts = record["facts"]
    affordance = record["affordance"]
    badges = "".join(_tag(label, facts[name]) for label, name in (
        ("bound", "bound"), ("policy active", "policy_active"),
        ("reachable", "reachable"), ("observed", "observed")))
    badges += f'<span class="tag {"yes" if affordance["kind"] in INVOKABLE else "warn"}">' \
               f'{_e(affordance["kind"])}</span>'
    rows = [
        ("Address", f'<code>{_e(record["logical_endpoint"])}</code>'),
        ("Record digest", f'<code>{record["record_digest"]}</code>'),
        ("Authority", f'<code>{_e(record["required_authority"])}</code>'),
        ("Effect", _e(record["effect_class"])),
        ("Actors", ", ".join(map(_e, record["actor_kinds"]))),
        ("Subject / verb", f'<code>{_e(record["subject"])}</code> / {_e(record["crud"])}'),
        ("Kernel", ", ".join(map(_e, record["kernel_paradigms"]))),
        ("Transition", f'<code>{_e(record["kernel_transition"] or "unmapped")}</code>'),
        ("Preconditions", " ".join(f'<code>{_e(item)}</code>' for item in record["preconditions"]) or "none"),
        ("Refusals", " ".join(f'<code>{_e(item)}</code>' for item in record["refusals"]) or "none"),
        ("Legal choices", " ".join(f'<code>{_e(item)}</code>' for item in record["legal_choices"]) or "none"),
        ("Surface affordance", f'<code>{_e(affordance["kind"])}</code> — '
         f'{_e(affordance["explanation"])} '
         f'(<code>{_e(affordance["reason_code"])}</code>)'),
        ("Policy", _policy(record)),
        ("Observations", " ".join(map(_e, record["observation_ids"])) or "none admitted"),
        ("Sources", _sources(record)),
    ]
    body = "".join(f"<dt>{label}</dt><dd>{value}</dd>" for label, value in rows) + _try(record)
    return (f'<details class="op"><summary><code class="id">{_e(record["operation_id"])}</code>'
            f'{badges}</summary><div class="body"><dl>{body}</dl></div></details>')


def _seams(interface: dict[str, Any]) -> str:
    seams = interface["seams"]
    examples = seams["policy_active_not_reachable"][:4]
    examples_html = "".join(f"<li><code>{_e(item)}</code></li>" for item in examples)
    return (
        '<div class="note"><b>No universal health score.</b> '
        f'{len(seams["policy_active_not_reachable"])} policy-active operations have no exact '
        f'route; {len(seams["reachable_not_observed"])} reachable operation has no admitted '
        f'observation; {len(seams["unmapped_kernel_transition"])} operations have no named '
        f'Kernel transition.<ul>{examples_html}</ul></div>')


def _omissions(interface: dict[str, Any]) -> str:
    items = "".join(
        f'<li><code>{_e(item["code"])}</code> — {_e(item["explanation"])}</li>'
        for item in interface["omissions"]
    )
    return f'<div class="note"><b>Material omissions.</b><ul>{items}</ul></div>'


def render(interface: dict[str, Any]) -> str:
    """Build human HTML from the same records emitted to a Model binding."""
    node, kernel, counts = interface["node"], interface["kernel"], interface["counts"]
    tiles = "".join(f"<li><b>{counts[name]}</b><span>{label}</span></li>" for name, label in (
        ("declared", "declared"), ("bound", "Kernel-bound"),
        ("policy_active", "policy-active"), ("reachable", "reachable"),
        ("observed", "observed")))
    by_service: dict[str, list[dict[str, Any]]] = {}
    for operation in interface["operations"]:
        by_service.setdefault(operation["service_id"], []).append(operation)
    sections = []
    for service in sorted(by_service):
        sections.append(f"<h2>{_e(service)}</h2>")
        sections.extend(_operation(item) for item in by_service[service])
    return (
        f"<title>Soveraeign Node Interface</title><style>{STYLE}</style><main>"
        "<h1>Soveraeign Node Interface</h1>"
        '<p class="sub">One local whole, projected from governed sources. Rendering changes '
        "nothing; Root settles locally.</p>"
        '<div class="identity">'
        f'<div><small>Node</small><code>{_e(node["node_id"])}</code><br>{_e(node["display_name"])}</div>'
        f'<div><small>Local Root</small><code>{_e(node["root_seat"])}</code></div>'
        f'<div><small>Kernel closure</small><code>{kernel["closure_input_state_digest"][:16]}</code><br>'
        f'{kernel["participants"]} participants · {len(kernel["paradigms"])} paradigms</div></div>'
        f'<ul class="counts">{tiles}</ul>{_seams(interface)}{_omissions(interface)}'
        f'{"".join(sections)}'
        '<footer>Generated from <code>contracts/fixtures/node-interface.reference.json</code> '
        "and rebuilt from its authored inputs at check time. Human and Model renderings resolve "
        "the same operation records and digests. This projection grants nothing, opens nothing, "
        "settles nothing, and is not an observation.</footer></main>")
