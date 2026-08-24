"""Render the operation surface as one self-contained HTML page.

The page is a Projection: it holds no standing, and rebuilding it from the same
inputs produces the same bytes. Nothing here decides anything. Where the
capability map and the gateway manifest disagree about whether an operation is
reachable, the page shows both claims side by side rather than picking one,
because choosing between them is Bdo's judgement.

No external stylesheet, script, or font. The page renders offline from a file
URL, and in either colour scheme.
"""

from __future__ import annotations

from typing import Any
import html


STYLE = """
:root {
  --bg: #fbfbf9; --fg: #1a1a18; --muted: #6b6b64; --line: #dedcd4;
  --card: #ffffff; --accent: #2f5d50; --warn: #8a4b1f; --off: #9a9a92;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #16161a; --fg: #e8e8e4; --muted: #9a9a93; --line: #2e2e34;
    --card: #1d1d22; --accent: #7fc0ac; --warn: #d69a63; --off: #6a6a63;
  }
}
* { box-sizing: border-box; }
body { margin: 0; padding: 2rem 1.25rem 4rem; background: var(--bg); color: var(--fg);
  font: 15px/1.55 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 62rem; margin: 0 auto; }
h1 { font-size: 1.5rem; margin: 0 0 .25rem; letter-spacing: -.01em; }
h2 { font-size: 1.05rem; margin: 2.5rem 0 .75rem; padding-bottom: .35rem;
  border-bottom: 1px solid var(--line); }
p.sub { color: var(--muted); margin: 0 0 1.5rem; }
.counts { display: flex; flex-wrap: wrap; gap: .5rem; margin: 0 0 1.5rem; padding: 0; list-style: none; }
.counts li { border: 1px solid var(--line); border-radius: .4rem; padding: .5rem .7rem;
  background: var(--card); }
.counts b { display: block; font-size: 1.35rem; font-weight: 650; }
.counts span { color: var(--muted); font-size: .8rem; }
.note { border-left: 3px solid var(--warn); background: var(--card); padding: .8rem 1rem;
  margin: 0 0 2rem; border-radius: 0 .4rem .4rem 0; }
.note h3 { margin: 0 0 .35rem; font-size: .95rem; color: var(--warn); }
.note p { margin: 0 0 .4rem; }
.note ul { margin: .4rem 0 0; padding-left: 1.1rem; }
.op { border: 1px solid var(--line); border-radius: .5rem; background: var(--card);
  margin-bottom: .55rem; overflow: hidden; }
.op > summary { cursor: pointer; padding: .6rem .8rem; display: flex; flex-wrap: wrap;
  gap: .55rem; align-items: baseline; }
.op > summary::marker { color: var(--muted); }
.op code.id { font: 13px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 600; }
.op .why { color: var(--muted); font-size: .82rem; }
.body { padding: 0 .8rem .8rem; border-top: 1px solid var(--line); }
dl { display: grid; grid-template-columns: 10rem 1fr; gap: .3rem .9rem; margin: .8rem 0 0; }
dt { color: var(--muted); font-size: .82rem; }
dd { margin: 0; font-size: .88rem; }
code { font: 12.5px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace;
  background: var(--bg); border: 1px solid var(--line); border-radius: .25rem; padding: .05rem .3rem; }
.tag { font-size: .72rem; letter-spacing: .03em; text-transform: uppercase; padding: .1rem .4rem;
  border-radius: .25rem; border: 1px solid var(--line); color: var(--muted); white-space: nowrap; }
.tag.live { color: var(--accent); border-color: var(--accent); }
.tag.off { color: var(--off); }
.tag.warn { color: var(--warn); border-color: var(--warn); }
.try { margin: .8rem 0 0; }
.try pre { margin: .35rem 0 0; padding: .6rem .7rem; overflow-x: auto; background: var(--bg);
  border: 1px solid var(--line); border-radius: .35rem;
  font: 12.5px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--line);
  color: var(--muted); font-size: .82rem; }
"""


NEWLINE = "\n"


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _tag(text: str, kind: str = "") -> str:
    return f'<span class="tag {kind}">{_e(text)}</span>'


def _transports(capability: dict[str, Any]) -> str:
    marks = []
    for endpoint in capability.get("endpoints", []):
        activation = endpoint.get("activation", "")
        kind = {"ACTIVE": "live"}.get(activation, "warn" if "REFUSED" in activation else "off")
        marks.append(_tag(f"{endpoint['transport']} {activation.lower().replace('_', ' ')}", kind))
    return " ".join(marks)


def _rows(capability: dict[str, Any], detail: dict[str, Any]) -> str:
    pairs: list[tuple[str, str]] = [
        ("Service standing", _e(capability.get("service_standing", "unknown"))),
        ("Required grant", f"<code>{_e(capability.get('required_authority', 'none'))}</code>"),
        ("Effect", _e(capability.get("effect_class", "unknown"))),
        ("Callers", ", ".join(_e(k) for k in capability.get("actor_kinds", [])) or "unstated"),
        ("Office", f"{_e(capability.get('office', ''))} / {_e(capability.get('counter', ''))}"),
    ]
    if detail.get("crud"):
        pairs.append(("Verb", _e(detail["crud"])))
    if detail.get("subject"):
        pairs.append(("Acts on", f"<code>{_e(detail['subject'])}</code>"))
    if detail.get("commit"):
        pairs.append(("Commits", _e(detail["commit"])))
    if detail.get("preconditions"):
        pairs.append(("Needs first",
                      " ".join(f"<code>{_e(p)}</code>" for p in detail["preconditions"])))
    if detail.get("refusals"):
        pairs.append(("Refuses with",
                      " ".join(f"<code>{_e(r)}</code>" for r in detail["refusals"])))
    if detail.get("kernel_transition"):
        pairs.append(("Kernel transition", f"<code>{_e(detail['kernel_transition'])}</code>"))
    if detail.get("requirement"):
        pairs.append(("Requirement", _e(detail["requirement"])))
    pairs.append(("Ways in", _transports(capability) or "none declared"))
    return "".join(f"<dt>{label}</dt><dd>{value}</dd>" for label, value in pairs)


def _operation(capability: dict[str, Any], detail: dict[str, Any],
               served: dict[str, Any] | None) -> str:
    badge = _tag("served now", "live") if served else _tag("not reachable", "off")
    try_block = ""
    if served:
        # A read needs neither a session nor a grant, so its command should not
        # tell a reader to open one.
        needs_session = (served.get("tier") != "read"
                         and served.get("requires_session", True))
        tail = " --session SESSION_ID" if needs_session else ""
        opens = ("python scripts/sov_surface.py try authority_open_session "
                 "participant=you model_identity=your-model" + NEWLINE) if needs_session else ""
        arguments = " ".join(f"{name}=..." for name, spec in served.get("arguments", {}).items()
                             if spec.get("required"))
        try_block = (
            '<div class="try"><dt>Try it</dt>'
            f'<pre>{_e(opens)}python scripts/sov_surface.py try {_e(served["tool"])}'
            f'{" " + _e(arguments) if arguments else ""}{_e(tail)}</pre></div>')
    return (
        f'<details class="op"><summary>'
        f'<code class="id">{_e(capability["capability_id"])}</code>{badge}'
        f'<span class="why">{_e(detail.get("logical_endpoint", ""))}</span>'
        f'</summary><div class="body"><dl>{_rows(capability, detail)}</dl>{try_block}'
        f'</div></details>')


def _disagreement(gap: dict[str, list[str]]) -> str:
    if not gap["map_says_off"] and not gap["undeclared"]:
        return ""
    parts = ['<div class="note"><h3>Two records disagree about this surface</h3>']
    if gap["map_says_off"]:
        parts.append(
            "<p>The capability map marks the MCP way in as declared-but-not-activated, "
            "while the gateway is serving these now:</p><ul>"
            + "".join(f"<li><code>{_e(name)}</code></li>" for name in gap["map_says_off"])
            + "</ul>")
    if gap["undeclared"]:
        parts.append(
            "<p>The gateway serves these, and no service manifest declares them as "
            "operations, so they appear nowhere in the map:</p><ul>"
            + "".join(f"<li><code>{_e(name)}</code></li>" for name in gap["undeclared"])
            + "</ul>")
    parts.append("<p>Which record is right is Bdo's to settle. This page states both.</p></div>")
    return "".join(parts)


def render(surface: dict[str, Any]) -> str:
    """Build the whole page from a joined surface. Same input, same bytes."""
    counts = surface["counts"]
    tiles = "".join(
        f"<li><b>{value}</b><span>{_e(label)}</span></li>"
        for label, value in (
            ("declared operations", counts["declared"]),
            ("served by the gateway", counts["served"]),
            ("services", counts["services"]),
            ("built services", counts["built_services"]),
            ("undeclared endpoints", counts["undeclared"]),
        ))
    sections = []
    for service_id in surface["services"]:
        operations = surface["by_service"][service_id]
        standing = operations[0]["capability"].get("service_standing", "unknown")
        sections.append(f"<h2>{_e(service_id)} <span class=\"tag\">{_e(standing)}</span></h2>")
        sections.extend(
            _operation(item["capability"], item["detail"], item["served"]) for item in operations)
    return (
        f"<title>Soveraeign Operation Surface</title><style>{STYLE}</style>"
        "<main><h1>Soveraeign operation surface</h1>"
        f'<p class="sub">{counts["declared"]} declared operations across '
        f'{counts["services"]} services, and the {counts["served"]} an operator can reach '
        "through the gateway today. Rebuilt from the manifests; it settles nothing.</p>"
        f'<ul class="counts">{tiles}</ul>'
        f'{_disagreement(surface["gap"])}'
        f"{''.join(sections)}"
        '<footer>Generated by <code>scripts/sov_surface.py render</code> from '
        "<code>contracts/fixtures/capability-map.reference.json</code>, the service manifests, "
        "and <code>bindings/mcp/manifest.json</code>. A projection: rebuildable, and never "
        "authoritative over the files it reads.</footer></main>")
