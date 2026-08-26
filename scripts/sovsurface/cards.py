"""The Node operation adapter: one interface operation becomes one Collection record.

Operations reach the surface through the same Collection mechanism as sessions.
Nothing here reinterprets the canonical Node Interface. A route affordance stays
the affordance the interface derived, and an operation the interface did not make
reachable stays non-invokable on this surface.

Two separate facts decide whether a card offers an invocation, and the card
states both. ``route_affordance`` is actor-neutral: it says whether an exact
policy-active route exists. ``binding_admission`` is actor-kind specific: it says
whether this binding's actor kind is admitted at all. This workspace is the Human
Binding, so an operation whose capability policy never admits HUMAN carries no
invocation here however reachable its route is.
"""

from __future__ import annotations

from typing import Any

from sovnode.affordances import INVOKABLE, binding_admission
from sovsurface.collection import Affordance, Record, Section
from sovsurface.primitives import code, e

BINDING = "HUMAN"
"""The actor kind this surface renders for. It is stated, never widened."""

SOURCE = "sov_surface.surface() — canonical Node Interface projection"


def _flag(value: Any) -> tuple[str, ...]:
    return ("true",) if value else ("false",)


def _policy(record: dict[str, Any]) -> str:
    rendered = []
    for endpoint in record["policy_endpoints"]:
        active = endpoint["activation"] == "ACTIVE"
        refused = endpoint["activation"].startswith("REFUSED")
        tone = "positive" if active else "warning" if refused else "muted"
        label = f'{endpoint["transport"]} {endpoint["activation"].lower().replace("_", " ")}'
        rendered.append(f'<span class="badge {tone}">{e(label)}</span>')
    return " ".join(rendered) or "none declared"


def _sources(record: dict[str, Any]) -> str:
    rows = "".join(
        f'<div class="source-row">{code(source["digest"][:12])}'
        f'<span>{e(source["address"])}</span></div>'
        for source in record["sources"]
    )
    return f'<div class="source-list">{rows}</div>'


def _invoke_affordance(record: dict[str, Any]) -> Affordance:
    """State the invocation an operation actually offers, and grant none of it."""
    kind = record["route_affordance"]["kind"]
    if kind not in INVOKABLE:
        return Affordance(
            f"Invoke {record['operation_id']}",
            detail=(
                f"The interface derived {kind} for this operation "
                f'({record["route_affordance"]["reason_code"]}). '
                "The surface does not widen it."
            ),
            available=False,
        )
    admission = binding_admission(record, BINDING)
    if not admission["admitted"]:
        return Affordance(
            f"Invoke {record['operation_id']}",
            detail=(
                f"An exact route is active, but {BINDING} is not admitted by this "
                f'operation capability policy ({admission["reason_code"]}). '
                "The surface does not widen it."
            ),
            available=False,
        )
    route = next(route for route in record["reachability"] if route["policy_active"])
    arguments = " ".join(f"{name}=..." for name in route["required_arguments"])
    return Affordance(
        f"Invoke {record['operation_id']}",
        command=(
            f"python scripts/sov_surface.py try {record['operation_id']} {arguments} "
            "--binding HUMAN --actor YOUR_ACTOR --scope YOUR_SCOPE"
        ),
        detail=(
            "Requires authority already recorded for that actor and scope. "
            "The surface creates none."
        ),
    )


def operation_record(record: dict[str, Any]) -> Record:
    """One operation card and inspector, built from the interface record itself."""
    facts, affordance = record["facts"], record["route_affordance"]
    admission = binding_admission(record, BINDING)
    kind = affordance["kind"]
    badges = tuple(
        (label, "positive" if facts[name] else "muted")
        for label, name in (
            ("bound", "bound"),
            ("policy active", "policy_active"),
            ("reachable", "reachable"),
            ("observed", "observed"),
        )
    ) + (
        (kind, "positive" if kind in INVOKABLE else "warning"),
        (f"{BINDING.lower()} binding", "positive" if admission["admitted"] else "warning"),
    )
    sections = (
        Section(
            "Identity",
            (
                ("Operation", code(record["operation_id"])),
                ("Address", code(record["logical_endpoint"])),
                ("Record digest", code(record["record_digest"])),
                ("Subject / verb", f'{code(record["subject"])} / {e(record["crud"])}'),
            ),
        ),
        Section(
            "Authority",
            (
                ("Required", code(record["required_authority"])),
                ("Effect", e(record["effect_class"])),
                ("Actors", ", ".join(map(e, record["actor_kinds"]))),
                ("Kernel", ", ".join(map(e, record["kernel_paradigms"]))),
                ("Transition", code(record["kernel_transition"] or "unmapped")),
            ),
            note="Reading this card records no grant and consumes none.",
        ),
        Section(
            "Reachability",
            (
                (
                    "Preconditions",
                    " ".join(code(item) for item in record["preconditions"]) or "none",
                ),
                ("Refusals", " ".join(code(item) for item in record["refusals"]) or "none"),
                (
                    "Legal choices",
                    " ".join(code(item) for item in record["legal_choices"]) or "none",
                ),
                ("Policy", _policy(record)),
            ),
        ),
        Section(
            "Affordance",
            (
                ("Route kind", code(kind)),
                ("Because", e(affordance["explanation"])),
                ("Reason code", code(affordance["reason_code"])),
                (
                    f"{BINDING} binding",
                    code("ADMITTED" if admission["admitted"] else "NOT ADMITTED"),
                ),
                ("Admission because", e(admission["explanation"])),
                ("Admission code", code(admission["reason_code"])),
            ),
            note=(
                ""
                if admission["admitted"]
                else f"{BINDING} is not admitted here, so this surface offers no "
                "invocation whatever the route says."
            ),
        ),
        Section(
            "Observations",
            tuple(
                (observation, code("admitted")) for observation in record["observation_ids"]
            ),
            note=(
                ""
                if record["observation_ids"]
                else "No observation is admitted. Self-test evidence is not an observation."
            ),
        ),
        Section("Sources", (("Declared by", _sources(record)),)),
    )
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
            admission["reason_code"],
            *record["kernel_paradigms"],
            *record["preconditions"],
            *record["refusals"],
        )
    )
    return Record(
        identity=record["operation_id"],
        kind="operation",
        title=record["operation_id"],
        eyebrow=f'{record["subject"]} · {record["crud"]}',
        badges=badges,
        search=search,
        facets={
            "kind": ("operation",),
            "service": (record["service_id"],),
            "affordance": (kind,),
            "binding": ((BINDING.lower(),) if admission["admitted"] else ("none",)),
            "subject": (record["subject"],),
            "authority": (record["required_authority"],),
            "crud": (record["crud"],),
            "effect": (record["effect_class"],),
            "reachable": _flag(facts["reachable"]),
            "observed": _flag(facts["observed"]),
        },
        sections=sections,
        affordances=(_invoke_affordance(record),),
    )
