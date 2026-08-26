"""Assemble one reconciliation survey of the projected epic tree."""

from __future__ import annotations

from pathlib import Path

from sovepic import projection, walk
from sovepic.projection import Issue


WORKABLE_KINDS = ("bit", "implementation-stub", "unblock")


def _horizon_rank(issue: Issue) -> int:
    order = {"NOW": 0, "NOW_TO_NEXT": 1, "NEXT": 2, "NOW_TO_SCALE_TRUST": 3}
    return order.get((issue.metadata or {}).get("horizon", ""), 4)


def survey(root: Path, document: dict, routing: dict) -> dict:
    """Reconcile the projection and select the reachable work.

    Open workable issues land in exactly one of four buckets - ``ready``,
    ``held``, ``unrouted``, ``owner_held`` - and every entry also carries the two
    independent readings ``routing`` and ``readiness`` (``walk.reading``). Only
    ``owner_held`` waits on Bdo.
    """
    schema = walk.load_issue_schema(root)
    by_number = projection.issues(document)
    root_issue = document["source"]["root_issue"]
    unmet = walk.readiness(by_number)

    contract, labels = [], []
    for number, issue in sorted(by_number.items()):
        if issue.state == "CLOSED":
            continue
        for defect in walk.metadata_defects(issue, schema):
            contract.append(f"#{number}: {defect}")
        for defect in walk.label_defects(issue):
            labels.append(f"#{number}: {defect}")

    ready, held, unrouted, owner_held = [], [], [], []
    for number, issue in sorted(by_number.items()):
        block = issue.metadata or {}
        if issue.state != "OPEN" or block.get("kind") not in WORKABLE_KINDS:
            continue
        domain = walk.route(issue, routing)
        blockers = unmet.get(number, [])
        entry = {
            "issue": number,
            "title": issue.title,
            "kind": block.get("kind"),
            "village": block.get("village"),
            "horizon": block.get("horizon"),
            "standing": block.get("standing"),
            "domain": domain,
            "blocked_by": blockers,
        }
        entry.update(walk.reading(domain, blockers))
        # The buckets are a dispatch projection over the two readings above, in
        # the order that decides who moves the issue next. Every entry still
        # carries both readings, so an unrouted issue that is also held reports
        # readiness HELD rather than hiding it behind the missing domain.
        if walk.owner_held(issue):
            owner_held.append(entry)
        elif domain is None:
            unrouted.append(entry)
        elif blockers:
            held.append(entry)
        else:
            ready.append(entry)

    stories = []
    for number, issue in sorted(by_number.items()):
        block = issue.metadata or {}
        if issue.state != "OPEN" or block.get("kind") != "story":
            continue
        reading, short = walk.story_reading(issue, by_number)
        stories.append(
            {
                "issue": number,
                "title": issue.title,
                "actor_kind": block.get("actor_kind"),
                "role": block.get("role"),
                "counter": block.get("parent"),
                "reading": reading,
                "short": short,
                "asks": [ask.get("of") for ask in block.get("asks") or []],
            }
        )

    ready.sort(key=lambda e: (_horizon_rank(by_number[e["issue"]]), e["issue"]))
    workable = ready + held + unrouted + owner_held
    return {
        "root_issue": root_issue,
        "synced_at": document["synced_at"],
        # ``ready``/``held``/``unrouted``/``owner_held`` count the dispatch buckets and
        # partition the workable issues. ``dependency_held`` and ``no_domain_owner``
        # count the readings instead, and deliberately overlap the buckets: an issue in
        # the unrouted bucket can still be dependency-held, and the bucket count alone
        # would understate the dependency work by exactly those issues.
        "counts": {
            "issues": len(by_number),
            "open": sum(1 for i in by_number.values() if i.state == "OPEN"),
            "ready": len(ready),
            "held": len(held),
            "unrouted": len(unrouted),
            "owner_held": len(owner_held),
            "dependency_held": sum(1 for e in workable if e["readiness"] == walk.HELD),
            "no_domain_owner": sum(1 for e in workable if e["routing"] == walk.UNROUTED),
            "stories": len(stories),
        },
        "contract_defects": contract,
        "label_defects": labels,
        "containment_defects": walk.containment_defects(by_number, root_issue),
        "ready": ready,
        "held": held,
        "unrouted": unrouted,
        "owner_held": owner_held,
        "stories": stories,
    }
