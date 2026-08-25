"""Domain cards composed from the canonical Node Interface records."""

from __future__ import annotations

from collections import Counter
from typing import Any

from sovnode.affordances import INVOKABLE
from sovsurface.primitives import badge, code, definition_rows, e, panel


def _policy(record: dict[str, Any]) -> str:
    rendered = []
    for endpoint in record["policy_endpoints"]:
        active = endpoint["activation"] == "ACTIVE"
        refused = endpoint["activation"].startswith("REFUSED")
        tone = "positive" if active else "warning" if refused else "muted"
        rendered.append(
            badge(
                f'{endpoint["transport"]} {endpoint["activation"].lower().replace("_", " ")}',
                tone,
            )
        )
    return " ".join(rendered)


def _sources(record: dict[str, Any]) -> str:
    rows = "".join(
        f'<div class="source-row">{code(source["digest"][:12])}'
        f'<span>{e(source["address"])}</span></div>'
        for source in record["sources"]
    )
    return f'<div class="source-list">{rows}</div>'


def _invoke(record: dict[str, Any]) -> str:
    if record["affordance"]["kind"] not in INVOKABLE:
        return ""
    route = next(route for route in record["reachability"] if route["policy_active"])
    arguments = " ".join(f"{name}=..." for name in route["required_arguments"])
    command = (
        f"python scripts/sov_surface.py try {record['operation_id']} {arguments} "
        "--binding HUMAN --actor YOUR_ACTOR --scope YOUR_SCOPE"
    )
    return (
        "<dt>Invoke</dt><dd>"
        f'<pre class="command">{e(command)}</pre>'
        '<span class="boundary">Requires authority already recorded for that actor and scope. '
        "The surface creates none.</span></dd>"
    )


def operation_card(record: dict[str, Any]) -> str:
    """Render one operation without changing or augmenting its affordance."""
    facts = record["facts"]
    affordance = record["affordance"]
    kind = affordance["kind"]
    tone = "positive" if kind in INVOKABLE else "warning"
    state_badges = "".join(
        badge(label, "positive" if facts[name] else "muted")
        for label, name in (
            ("bound", "bound"),
            ("policy active", "policy_active"),
            ("reachable", "reachable"),
            ("observed", "observed"),
        )
    )
    state_badges += badge(kind, tone)
    rows = [
        ("Address", code(record["logical_endpoint"])),
        ("Record digest", code(record["record_digest"])),
        ("Authority", code(record["required_authority"])),
        ("Effect", e(record["effect_class"])),
        ("Actors", ", ".join(map(e, record["actor_kinds"]))),
        ("Subject / verb", f'{code(record["subject"])} / {e(record["crud"])}'),
        ("Kernel", ", ".join(map(e, record["kernel_paradigms"]))),
        ("Transition", code(record["kernel_transition"] or "unmapped")),
        (
            "Preconditions",
            " ".join(code(item) for item in record["preconditions"]) or "none",
        ),
        ("Refusals", " ".join(code(item) for item in record["refusals"]) or "none"),
        (
            "Legal choices",
            " ".join(code(item) for item in record["legal_choices"]) or "none",
        ),
        (
            "Surface affordance",
            f'{code(kind)} — {e(affordance["explanation"])} '
            f'({code(affordance["reason_code"])})',
        ),
        ("Policy", _policy(record)),
        (
            "Observations",
            " ".join(map(e, record["observation_ids"])) or "none admitted",
        ),
        ("Sources", _sources(record)),
    ]
    body = definition_rows(rows)
    body = body[:-5] + _invoke(record) + "</dl>"
    search = " ".join(
        (
            record["operation_id"],
            record["service_id"],
            record["subject"],
            record["crud"],
            record["required_authority"],
            record["effect_class"],
            kind,
            affordance["reason_code"],
            *record["kernel_paradigms"],
            *record["preconditions"],
            *record["refusals"],
        )
    ).lower()
    return (
        '<details class="op card" data-card="operation" '
        f'data-kind="operation" data-service="{e(record["service_id"])}" '
        f'data-affordance="{e(kind)}" data-subject="{e(record["subject"])}" '
        f'data-authority="{e(record["required_authority"])}" '
        f'data-search="{e(search)}">'
        '<summary><span class="card-leading">'
        f'{code(record["operation_id"], "id")}<span class="operation-subject">'
        f'{e(record["subject"])} · {e(record["crud"])}</span></span>'
        f'<span class="badges">{state_badges}</span></summary>'
        f'<div class="op-body">{body}</div></details>'
    )


def service_card(service: str, operations: list[dict[str, Any]]) -> str:
    kinds = Counter(item["affordance"]["kind"] for item in operations)
    reachable = sum(item["facts"]["reachable"] for item in operations)
    subjects = sorted({item["subject"] for item in operations})
    chips = " ".join(
        badge(f"{count} {kind.lower()}", "positive" if kind in INVOKABLE else "muted")
        for kind, count in sorted(kinds.items())
    )
    subject_preview = ", ".join(subjects[:6])
    if len(subjects) > 6:
        subject_preview += f" +{len(subjects) - 6}"
    body = (
        f'<div class="card-statline"><b>{len(operations)}</b> operations · '
        f"<b>{reachable}</b> exact routes</div>"
        f'<div class="badges">{chips}</div>'
        f'<p class="muted">Subjects: {e(subject_preview or "none")}</p>'
        f'<button class="text-action" type="button" data-filter="service:{e(service)}">'
        "Browse service</button>"
    )
    return (
        f'<article class="card browse-card" data-card="service" data-kind="service" '
        f'data-service="{e(service)}" data-search="{e((service + " " + subject_preview).lower())}">'
        f'<div class="eyebrow">service</div><h3>{e(service)}</h3>{body}</article>'
    )


def subject_card(subject: str, operations: list[dict[str, Any]]) -> str:
    services = sorted({item["service_id"] for item in operations})
    kinds = Counter(item["affordance"]["kind"] for item in operations)
    body = (
        f'<p><b>{len(operations)}</b> operations across {e(", ".join(services))}</p>'
        f'<div class="badges">'
        + " ".join(badge(f"{count} {kind.lower()}") for kind, count in sorted(kinds.items()))
        + "</div>"
        f'<button class="text-action" type="button" data-filter="subject:{e(subject)}">'
        "Browse subject</button>"
    )
    search = f"{subject} {' '.join(services)}".lower()
    return (
        f'<article class="card browse-card" data-card="subject" data-kind="subject" '
        f'data-subject="{e(subject)}" data-search="{e(search)}">'
        f'<div class="eyebrow">declared subject</div><h3>{e(subject)}</h3>{body}</article>'
    )


def omission_card(item: dict[str, Any]) -> str:
    return panel(
        item["code"],
        f'<p class="muted">{e(item["explanation"])}</p>',
        eyebrow="material omission",
        css="omission",
        component="omission-card",
    )
