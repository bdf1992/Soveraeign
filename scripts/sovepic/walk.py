"""Reconcile the projected epic tree against its contracts and select work.

Three independent readings, none of which settles anything:

* metadata - each issue's declared block against ``contracts/issue-metadata.schema.json``;
* projection - the visible GitHub labels against the block they project;
* containment - the epic -> village -> bit/stub tree against the declared parents.

Selection then keeps three states apart, because merging any two of them sends
ordinary work to the owner:

* ``HELD`` - an unsatisfied ``requires`` edge;
* ``UNROUTED`` - no repository artifact evidences a domain owner;
* ``OWNER_HELD`` - an open ``unblock`` ticket asking the owner for a judgement.

Routing and readiness are independent readings of the same issue: an issue can be
``UNROUTED`` and ``HELD`` at once. Only ``OWNER_HELD`` waits on Bdo. Reachability
is evidence about the tree, not a grant: an issue being ready says nothing about
whether an open decision in ``STATUS.yaml`` admits the work.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from sovepic.projection import Issue
from sovschedule import jsonshape


ISSUE_SCHEMA_PATH = Path("contracts") / "issue-metadata.schema.json"

# Projections owned by .github/labels.yml and CONTRIBUTING.md; restated here only
# for machine comparison. scripts/tests/test_sov_epic.py asserts every name below
# still exists in the catalogue, so this table cannot drift from it silently.
KIND_LABEL = {
    "epic-of-epics": "type: epic",
    "village": "type: village",
    "bit": "type: bit",
    "implementation-stub": "type: stub",
    "story": "type: story",
    "unblock": "type: unblock",
}
VILLAGE_LABEL = {
    "ground-and-evidence": "village: ground",
    "trust-and-control": "village: trust",
    "reach-and-motion": "village: motion",
    "domain-and-qualification": "village: domain",
}
HORIZON_LABEL = {
    "NOW": "horizon: now",
    "NEXT": "horizon: next",
    "ON_SCALE_TRUST": "horizon: scale-trust",
    "NOW_TO_NEXT": "horizon: spanning",
    "NEXT_TO_SCALE_TRUST": "horizon: spanning",
    "NOW_TO_SCALE_TRUST": "horizon: spanning",
}
EFFECT_LABEL = {
    "CONTROL": "effect: control",
    "OBSERVE_ONLY": "effect: observe-only",
    "REQUEST_ONLY": "effect: request-only",
    "BOUNDED_EXECUTION": "effect: bounded-execution",
    "EXTERNAL_BOUNDARY": "effect: external-boundary",
}
DEFAULT_EFFECT = "RECORD_LOCAL"
UNPROJECTED_EFFECTS = ("RESOURCE_CONSUMPTION", "EXTERNAL_WORLD")
SATISFYING_STANDINGS = frozenset(
    {"BUILT_SELF_TESTED_NOT_WITNESSED", "WITNESSED", "RATIFIED"}
)

# The three states this module refuses to conflate, plus the two values each of the
# independent readings can take. ROUTED/UNROUTED answers who owns the work;
# REACHABLE/HELD answers whether its prerequisites are satisfied; OWNER_HELD is a
# third thing neither reading may imply.
ROUTED = "ROUTED"
UNROUTED = "UNROUTED"
REACHABLE = "REACHABLE"
HELD = "HELD"
OWNER_HELD = "OWNER_HELD"


def load_issue_schema(root: Path) -> dict:
    """Read the issue metadata contract."""
    return json.loads((root / ISSUE_SCHEMA_PATH).read_text(encoding="utf-8"))


def _reference(value: Any) -> int | None:
    if isinstance(value, str) and value.startswith("#") and value[1:].isdigit():
        return int(value[1:])
    return None


def metadata_defects(issue: Issue, schema: dict) -> list[str]:
    """Contract defects in one issue's declared block."""
    if issue.parse_error:
        return [f"metadata unreadable: {issue.parse_error}"]
    if issue.metadata is None:
        return ["no metadata block"]
    return jsonshape.check(issue.metadata, schema)


def label_defects(issue: Issue) -> list[str]:
    """Disagreements between the visible labels and the block they project."""
    block = issue.metadata or {}
    if not block:
        return []
    defects = []
    labels = set(issue.labels)
    expected = []
    if block.get("kind") in KIND_LABEL:
        expected.append(KIND_LABEL[block["kind"]])
    if block.get("village") in VILLAGE_LABEL:
        expected.append(VILLAGE_LABEL[block["village"]])
    if block.get("horizon") in HORIZON_LABEL:
        expected.append(HORIZON_LABEL[block["horizon"]])
    effect = block.get("effect_class")
    if effect in EFFECT_LABEL:
        expected.append(EFFECT_LABEL[effect])
    elif effect in UNPROJECTED_EFFECTS:
        defects.append(f"effect_class {effect} has no label in .github/labels.yml")
    for name in expected:
        if name not in labels:
            defects.append(f"missing label '{name}' projected by the metadata block")
    if effect == DEFAULT_EFFECT and f"effect: {DEFAULT_EFFECT.lower().replace('_', '-')}" in labels:
        defects.append("default effect label is shown; CONTRIBUTING.md omits it")
    for name in sorted(labels):
        if name.startswith("type: ") and name not in expected:
            defects.append(f"label '{name}' contradicts kind {block.get('kind')!r}")
        if name.startswith("village: ") and name not in expected:
            defects.append(f"label '{name}' contradicts village {block.get('village')!r}")
    return defects


def containment_defects(by_number: dict[int, Issue], root_issue: int) -> list[str]:
    """Breaks in the epic -> village -> bit/stub containment tree.

    ``village_issue`` is the containment edge for a bit or stub, not ``parent``:
    the schema lets a bit name the epic as its parent while its village issue is
    the node that must contain it. Closed issues are skipped - a demoted ticket
    is not a hole in the tree.
    """
    defects = []
    live = {n: i for n, i in by_number.items() if i.state != "CLOSED" and i.metadata}
    children: dict[int, set[int]] = {}
    for number, issue in sorted(live.items()):
        listed = {
            child
            for child in (_reference(v) for v in issue.metadata.get("child_issues") or [])
            if child is not None
        }
        children[number] = listed
        for child in sorted(listed):
            if child not in by_number:
                defects.append(f"#{number}: child #{child} is not present in the projection")
        for value in issue.metadata.get("requires") or []:
            required = _reference(value)
            if required is not None and required not in by_number:
                defects.append(f"#{number}: requires #{required}, which is not present")
        parent = _reference(issue.metadata.get("parent"))
        if number != root_issue and parent is None:
            defects.append(f"#{number}: declares no parent and is not the epic root")
        elif parent is not None and parent not in by_number:
            defects.append(f"#{number}: parent #{parent} is not present in the projection")

    villages = {n for n, i in live.items() if i.metadata.get("kind") == "village"}
    for number, issue in sorted(live.items()):
        if issue.metadata.get("kind") != "story":
            continue
        counter = _reference(issue.metadata.get("parent"))
        at = live.get(counter) if counter is not None else None
        if at is None or at.metadata.get("kind") != "bit":
            defects.append(f"#{number}: story parent #{counter} is not a live bit (the counter)")
        for value in issue.metadata.get("leans_on") or []:
            support = _reference(value)
            if support is not None and support not in by_number:
                defects.append(f"#{number}: leans on #{support}, which is not present")
    declared = children.get(root_issue, set())
    for missing in sorted(villages - declared):
        defects.append(f"#{root_issue}: village #{missing} is not listed in child_issues")
    for extra in sorted(declared - villages):
        defects.append(f"#{root_issue}: child #{extra} is not a village issue")

    for number, issue in sorted(live.items()):
        container = _reference(issue.metadata.get("village_issue"))
        if container is None:
            continue
        if container not in villages:
            defects.append(f"#{number}: village_issue #{container} is not a live village issue")
        elif number not in children.get(container, set()):
            defects.append(f"#{number}: village #{container} does not list it in child_issues")
    return defects


def route(issue: Issue, routing: dict) -> str | None:
    """Resolve the harness domain that owns an issue, or None when unrouted."""
    direct = routing.get("issue_routes", {}).get(str(issue.number))
    if direct:
        return direct["domain"]
    return None


def owner_held(issue: Issue) -> bool:
    """True only for an unblock ticket that asks the owner for a judgement.

    ``contracts/issue-metadata.schema.json`` is the authority: an unblock ticket
    whose ``requested_provision`` is ``judgement`` must name ``owner`` as its
    ``requested_from``, and judgement is asked of no other tier. Either key alone
    is taken as owner-held so a malformed ticket is withheld from dispatch rather
    than handed to a worker. Nothing else in the tree is owner-held: an
    unsatisfied dependency is HELD and a missing domain owner is UNROUTED, and
    neither reaches Bdo.
    """
    block = issue.metadata or {}
    if block.get("kind") != "unblock":
        return False
    return block.get("requested_from") == "owner" or block.get("requested_provision") == "judgement"


def reading(domain: str | None, blockers: list[str]) -> dict[str, str]:
    """The two independent readings of one workable issue.

    ``routing`` answers whether a repository artifact evidences a domain owner;
    ``readiness`` answers whether every ``requires`` edge is satisfied. They are
    never one field, because an issue with no domain owner can also be waiting on
    a prerequisite, and reporting only the first hides the second.
    """
    return {
        "routing": UNROUTED if domain is None else ROUTED,
        "readiness": HELD if blockers else REACHABLE,
    }


def _satisfied(required: int, by_number: dict[int, Issue]) -> bool:
    issue = by_number.get(required)
    if issue is None:
        return False
    if issue.state == "CLOSED":
        return True
    return (issue.metadata or {}).get("standing") in SATISFYING_STANDINGS


def readiness(by_number: dict[int, Issue]) -> dict[int, list[str]]:
    """Unsatisfied ``requires`` edges per open issue; an empty list means reachable."""
    result = {}
    for number, issue in sorted(by_number.items()):
        if issue.state != "OPEN" or not issue.metadata:
            continue
        blockers = []
        for value in issue.metadata.get("requires") or []:
            required = _reference(value)
            if required is not None and not _satisfied(required, by_number):
                blockers.append(f"#{required}")
        result[number] = blockers
    return result


def story_reading(issue: Issue, by_number: dict[int, Issue]) -> tuple[str, list[str]]:
    """Read one story as told, walkable, or walked, with the supports still short.

    A story is walkable when a scenario binds it and every support it leans on is at
    least BUILT; it is walked once a witness has observed the scenario. The reading is
    evidence about the tree, never a grant and never a settlement.
    """
    block = issue.metadata or {}
    short = [
        f"#{support}"
        for support in (_reference(v) for v in block.get("leans_on") or [])
        if support is not None and not _satisfied(support, by_number)
    ]
    if block.get("standing") in ("WITNESSED", "RATIFIED"):
        return "walked", short
    if block.get("scenario") and not short:
        return "walkable", short
    return "told", short
