"""Assemble one reconciliation survey of the projected epic tree."""

from __future__ import annotations

from pathlib import Path

from sovepic import projection, walk
from sovepic.projection import Issue


# The kinds the walk may select for a builder. A verification engagement is
# deliberately absent: SDLC.md requires the Red operator to be independent of the
# builder, and handing one to a sov-worker in a build walk would defeat that.
WORKABLE_KINDS = ("bit", "implementation-stub", "unblock", "chore")


def _horizon_rank(issue: Issue) -> int:
    order = {"NOW": 0, "NOW_TO_NEXT": 1, "NEXT": 2, "NOW_TO_SCALE_TRUST": 3}
    return order.get((issue.metadata or {}).get("horizon", ""), 4)


def survey(root: Path, document: dict, routing: dict) -> dict:
    """Reconcile the projection and select the reachable work."""
    schema = walk.load_issue_schema(root)
    label_projection = walk.load_label_projection(root)
    by_number = projection.issues(document)
    root_issue = document["source"]["root_issue"]
    blockers = walk.readiness(by_number)

    contract, labels = [], []
    for number, issue in sorted(by_number.items()):
        if issue.state == "CLOSED":
            continue
        for defect in walk.metadata_defects(issue, schema):
            contract.append(f"#{number}: {defect}")
        for defect in walk.label_defects(issue, label_projection):
            labels.append(f"#{number}: {defect}")

    ready, held, unrouted = [], [], []
    for number, issue in sorted(by_number.items()):
        block = issue.metadata or {}
        if issue.state != "OPEN" or block.get("kind") not in WORKABLE_KINDS:
            continue
        domain = walk.route(issue, routing)
        entry = {
            "issue": number,
            "title": issue.title,
            "kind": block.get("kind"),
            "village": block.get("village"),
            "horizon": block.get("horizon"),
            "standing": block.get("standing"),
            "domain": domain,
            "blocked_by": blockers.get(number, []),
        }
        if domain is None:
            unrouted.append(entry)
        elif entry["blocked_by"]:
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
    return {
        "root_issue": root_issue,
        "synced_at": document["synced_at"],
        "counts": {
            "issues": len(by_number),
            "open": sum(1 for i in by_number.values() if i.state == "OPEN"),
            "ready": len(ready),
            "held": len(held),
            "unrouted": len(unrouted),
            "stories": len(stories),
        },
        "contract_defects": contract,
        "label_defects": labels,
        "containment_defects": walk.containment_defects(by_number, root_issue),
        "ready": ready,
        "held": held,
        "unrouted": unrouted,
        "stories": stories,
    }
