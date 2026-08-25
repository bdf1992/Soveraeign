"""Service and subject cards, and the three Node Interface collections.

Services and subjects summarize operations; they never add an operation, an
authority, or an instance. A declared subject is a type, and this module keeps
the absence of instance reads visible rather than filling it with an example.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from sovnode.affordances import INVOKABLE
from sovsurface.cards import SOURCE, operation_record
from sovsurface.collection import Affordance, Collection, Record, Section
from sovsurface.primitives import code, e, panel

SERVICE_FACETS = ("kind", "service", "affordance", "subject")
SUBJECT_FACETS = ("kind", "service", "subject")

OPERATION_FACETS = (
    "kind",
    "service",
    "affordance",
    "subject",
    "authority",
    "crud",
    "effect",
    "reachable",
    "observed",
)


def service_record(service: str, operations: list[dict[str, Any]]) -> Record:
    """One service card over the operations the interface assigned to it."""
    kinds = Counter(item["affordance"]["kind"] for item in operations)
    reachable = sum(item["facts"]["reachable"] for item in operations)
    observed = sum(item["facts"]["observed"] for item in operations)
    subjects = sorted({item["subject"] for item in operations})
    authorities = sorted({item["required_authority"] for item in operations})
    preview = ", ".join(subjects[:6]) + (f" +{len(subjects) - 6}" if len(subjects) > 6 else "")
    return Record(
        identity=service,
        kind="service",
        title=service,
        eyebrow="service",
        summary=(
            f'<div class="card-statline"><b>{len(operations)}</b> operations · '
            f"<b>{reachable}</b> exact routes</div>"
            f'<p class="muted">Subjects: {e(preview or "none")}</p>'
        ),
        badges=tuple(
            (f"{count} {kind.lower()}", "positive" if kind in INVOKABLE else "muted")
            for kind, count in sorted(kinds.items())
        ),
        search=f"{service} {preview} {' '.join(authorities)}",
        facets={
            "kind": ("service",),
            "service": (service,),
            "affordance": tuple(sorted(kinds)),
            "subject": tuple(subjects),
        },
        sections=(
            Section(
                "Identity",
                (("Service", code(service)), ("Operations", code(len(operations)))),
            ),
            Section(
                "Reachability",
                (
                    ("Exact routes", code(reachable)),
                    ("Observed", code(observed)),
                    (
                        "Affordances",
                        ", ".join(f"{count} {kind}" for kind, count in sorted(kinds.items())),
                    ),
                ),
                note=(
                    ""
                    if reachable
                    else "Every operation on this service is declared and none is reachable."
                ),
            ),
            Section("Subjects", tuple((item, code("declared")) for item in subjects)),
            Section(
                "Authority",
                tuple((item, code("required")) for item in authorities),
                note="Authority the operations require. The surface holds none of it.",
            ),
            Section("Sources", (("Derived from", code(SOURCE)),)),
        ),
        affordances=(
            Affordance(
                "Browse this service",
                filter_value=f"service:{service}",
                detail="Query narrows what is shown. It activates no route.",
            ),
        ),
    )


def subject_record(subject: str, operations: list[dict[str, Any]]) -> Record:
    """One declared subject. Declared types are not live instances."""
    services = sorted({item["service_id"] for item in operations})
    kinds = Counter(item["affordance"]["kind"] for item in operations)
    verbs = sorted({item["crud"] for item in operations})
    return Record(
        identity=subject,
        kind="subject",
        title=subject,
        eyebrow="declared subject",
        summary=(
            f"<p><b>{len(operations)}</b> operations across {e(', '.join(services))}</p>"
        ),
        badges=tuple((f"{count} {kind.lower()}", "muted") for kind, count in sorted(kinds.items())),
        search=f"{subject} {' '.join(services)} {' '.join(verbs)}",
        facets={
            "kind": ("subject",),
            "service": tuple(services),
            "subject": (subject,),
        },
        sections=(
            Section(
                "Identity",
                (("Subject", code(subject)), ("Declared by", ", ".join(map(e, services)))),
            ),
            Section(
                "Operations",
                tuple(
                    (item["operation_id"], code(item["affordance"]["kind"]))
                    for item in operations
                ),
            ),
            Section(
                "Instances",
                (),
                note=(
                    "No instance read exists for this subject. A declared type is not a "
                    "live object, and the surface will not invent one."
                ),
            ),
            Section("Sources", (("Derived from", code(SOURCE)),)),
        ),
        affordances=(
            Affordance(
                "Browse this subject",
                filter_value=f"subject:{subject}",
                detail="Query narrows what is shown.",
            ),
            Affordance(
                f"List {subject} instances",
                detail="No governed instance read projection exists yet.",
                available=False,
            ),
        ),
    )


def service_collection(services: dict[str, list[dict[str, Any]]]) -> Collection:
    return Collection(
        collection_id="services",
        label="Services",
        description="Declared service boundaries, counted from their own operations.",
        source=SOURCE,
        records=tuple(service_record(name, ops) for name, ops in sorted(services.items())),
        facets=SERVICE_FACETS,
    )


def subject_collection(subjects: dict[str, list[dict[str, Any]]]) -> Collection:
    return Collection(
        collection_id="subjects",
        label="Subjects",
        description="Declared subjects only. Object instances remain an explicit omission.",
        source=SOURCE,
        records=tuple(subject_record(name, ops) for name, ops in sorted(subjects.items())),
        facets=SUBJECT_FACETS,
        omissions=(
            "No governed object-instance read projection exists. Asset, Version, "
            "Derivative, Lineage, and Receipt browsing waits on that source, and is "
            "not simulated here.",
        ),
    )


def operation_collection(operations: list[dict[str, Any]]) -> Collection:
    return Collection(
        collection_id="operations",
        label="Operations",
        description="Expand a card to inspect exact authority, route, refusal, and source.",
        source=SOURCE,
        records=tuple(operation_record(item) for item in operations),
        facets=OPERATION_FACETS,
        layout="row",
    )


def omission_card(item: dict[str, Any]) -> str:
    """A material omission the canonical interface itself declared."""
    return panel(
        item["code"],
        f'<p class="muted">{e(item["explanation"])}</p>',
        eyebrow="material omission",
        css="omission",
        component="omission-card",
    )
