"""Turn a captured coordination surface into recommended actions with their evidence.

The survey runs entirely offline against a registrar export. It judges only what the
contracts in this checkout declare, and it says so when the board uses vocabulary the
checkout does not carry rather than recommending the board be cut down to fit.

Closed tickets are surveyed for nothing. A closed issue cannot drift, and judging one
produces a report that can never come back clean.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import json

from sovboard.actions import Action, Batch
from sovkernel.jsonschema import validate
from sovticket import labels as labelmod
from sovticket.yamlblock import TicketBlockError, load_ticket

#: Hours of silence after which an open pull request is surfaced for triage. Twelve
#: suits a repository where a feature lands in an afternoon; a slower one wants more.
#: The threshold is a reversible default, not a policy: it changes what gets reported
#: and never what gets executed, and ``review --stale-hours`` moves it without an edit.
STALE_HOURS = 12

RULE_LABELS = "CONTRIBUTING.md: labels are a projection of issue metadata, never a second authority"
RULE_CONTRACT = "contracts/issue-metadata.schema.json: every ticket opens with a valid soveraeign-ticket/v1 block"
RULE_BRANCH = "AGENTS.md, Branch and commit strategy: normal work uses a short-lived branch"
RULE_STALE = "AGENTS.md, Branch and commit strategy: do not use long-lived integration branches"
RULE_BEHIND = "AGENTS.md, Design System of Record: main is the releasable design System of Record"
RULE_CATALOGUE = ".github/labels.yml: the canonical label catalogue this repository projects onto"


def _parse_time(value: str | None) -> datetime | None:
    """Parse an ISO-8601 instant from the registrar, returning None when absent."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _open_issues(export: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the open issues in number order.

    A closed ticket owes no contract repair: authoring a block for work nobody will
    take is not work. Its labels are a different matter and are surveyed separately.
    """
    live = [item for item in export if (item.get("state") or "OPEN").upper() == "OPEN"]
    return sorted(live, key=lambda item: item["number"])


def _labelled_issues(export: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return every ticket whose labels are still on the board, open or closed.

    Closed tickets were surveyed for nothing at all, which made their labels the one
    part of the coordination surface that could drift with nothing watching. A closed
    ticket keeps its labels, keeps appearing under a standing filter, and keeps being
    read; #6, #7, and #51 each sat mislabelled and needed a hand-built action, because
    the survey that exists to catch exactly that could not see them (decisions/0090).
    """
    return sorted(export, key=lambda item: item["number"])


def survey_catalogue(root: Path, live: list[dict[str, Any]]) -> list[Action]:
    """Reconcile the declared label catalogue against the one the repository actually has.

    Nothing syncs ``.github/labels.yml`` to GitHub, so a label can be declared, projected,
    and still absent from the repository. Catching that here is the difference between a
    survey that is complete and one whose gap is discovered by a failed write.
    """
    declared = labelmod.load_catalogue_entries(root)
    present = {entry["name"] for entry in live}
    governed = tuple(labelmod.load_projection(root)["unprojected_label_prefixes"])
    actions: list[Action] = []
    for entry in declared:
        if entry["name"] in present:
            continue
        actions.append(
            Action(
                kind="LABEL_CREATE",
                target="repository",
                argument=entry["name"],
                extra=(("color", entry["color"]), ("description", entry["description"])),
                evidence="declared in .github/labels.yml; the repository has no such label",
                rule=RULE_CATALOGUE,
                recommendation=f"create {entry['name']!r} so the projection has something to apply",
            )
        )
    known = {entry["name"] for entry in declared}
    for entry in live:
        name = entry["name"]
        if name in known or not name.startswith(governed):
            continue
        actions.append(
            Action(
                kind="CATALOGUE_UNDECLARED",
                target="repository",
                argument=name,
                evidence=f"repository carries {name!r} in the governed namespace; the catalogue does not declare it",
                rule=RULE_CATALOGUE,
                recommendation=(
                    "declare it in .github/labels.yml, or merge the branch that already does; "
                    "deleting a label in use is a judgement, not a reconciliation"
                ),
            )
        )
    return actions


def survey_tickets(root: Path, export: list[dict[str, Any]]) -> list[Action]:
    """Recommend label reconciliation across every ticket; report contract defects on open ones.

    The two readings have different populations on purpose. A defect is work, and closed
    work is not taken. A label is a projection that stays visible after closing.
    """
    schema = json.loads((root / "contracts" / "issue-metadata.schema.json").read_text("utf-8"))
    projection = labelmod.load_projection(root)
    catalogue = labelmod.load_catalogue(root)
    actions: list[Action] = []
    open_numbers = {item["number"] for item in _open_issues(export)}
    for issue in _labelled_issues(export):
        ref = f"#{issue['number']}"
        closed = issue["number"] not in open_numbers
        try:
            metadata = load_ticket(issue.get("body") or "")
        except TicketBlockError as error:
            if closed:
                continue  # a closed ticket owes no block; there is no work to make visible
            actions.append(
                Action(
                    kind="CONTRACT_DEFECT",
                    target=ref,
                    evidence=f"metadata block unreadable: {error}",
                    rule=RULE_CONTRACT,
                    recommendation=(
                        "author a valid metadata block on this issue; until then it is "
                        "invisible to the work queue"
                    ),
                )
            )
            continue
        defects = validate(metadata, schema)
        if defects:
            if closed:
                continue
            actions.append(
                Action(
                    kind="CONTRACT_DEFECT",
                    target=ref,
                    evidence=f"metadata block fails the schema: {defects[0]}",
                    rule=RULE_CONTRACT,
                    recommendation="correct the metadata block; a batch approval cannot author it",
                )
            )
            continue
        actions.extend(_label_actions(ref, issue, metadata, projection, catalogue))
    return actions


def _label_actions(
    ref: str,
    issue: dict[str, Any],
    metadata: dict[str, Any],
    projection: dict[str, Any],
    catalogue: set[str],
) -> list[Action]:
    """Derive per-label add and remove recommendations for one conforming ticket."""
    live = [entry["name"] for entry in issue.get("labels", [])]
    drift = labelmod.compare(ref, metadata, live, projection)
    actions: list[Action] = []
    for value in drift.unmapped:
        actions.append(
            Action(
                kind="CONTRACT_BEHIND",
                target=ref,
                argument=value,
                evidence=f"metadata carries {value}, which this checkout's projection does not map",
                rule=RULE_BEHIND,
                recommendation=(
                    "extend contracts/ticket-label-projection.json, or merge the branch that "
                    "already does; do not strip the board to match a checkout that is behind"
                ),
            )
        )
    for name in drift.missing:
        if name not in catalogue:
            actions.append(
                Action(
                    kind="LABEL_UNMAPPED",
                    target=ref,
                    argument=name,
                    evidence=f"projection implies {name!r}, absent from .github/labels.yml",
                    rule=RULE_LABELS,
                    recommendation="declare the label in .github/labels.yml before projecting it",
                )
            )
            continue
        actions.append(
            Action(
                kind="LABEL_ADD",
                target=ref,
                argument=name,
                evidence=f"metadata implies {name!r}; the issue does not carry it",
                rule=RULE_LABELS,
                recommendation=f"add {name!r} so the visible label matches the metadata",
            )
        )
    for name in drift.unexpected:
        actions.append(
            Action(
                kind="LABEL_REMOVE",
                target=ref,
                argument=name,
                evidence=f"issue carries {name!r}; the metadata implies no such label",
                rule=RULE_LABELS,
                recommendation=f"remove {name!r}, or change the metadata that should imply it",
            )
        )
    return actions


def survey_branches(pulls: list[dict[str, Any]], branches: list[dict[str, Any]]) -> list[Action]:
    """Recommend deleting every remote branch whose pull request already merged."""
    merged = {
        pull["headRefName"]: pull["number"]
        for pull in pulls
        if (pull.get("state") or "").upper() == "MERGED" and pull.get("headRefName")
    }
    live = {branch["name"] for branch in branches}
    actions = []
    for name in sorted(merged):
        if name not in live:
            continue
        actions.append(
            Action(
                kind="BRANCH_DELETE",
                target=name,
                argument=name,
                evidence=f"pull request #{merged[name]} merged this branch and the ref still exists",
                rule=RULE_BRANCH,
                recommendation=f"delete origin/{name}; the merge commit keeps it recoverable",
            )
        )
    return actions


def survey_pulls(
    pulls: list[dict[str, Any]], now: datetime | None, stale_hours: int = STALE_HOURS
) -> list[Action]:
    """Report open pull requests that have gone quiet, so triage is a decision not a discovery."""
    if now is None:
        return []
    cutoff = now - timedelta(hours=stale_hours)
    actions = []
    for pull in sorted(pulls, key=lambda item: item["number"]):
        if (pull.get("state") or "").upper() != "OPEN":
            continue
        updated = _parse_time(pull.get("updatedAt"))
        if updated is None or updated > cutoff:
            continue
        age = int((now - updated).total_seconds() // 3600)
        state = "draft" if pull.get("isDraft") else "open"
        actions.append(
            Action(
                kind="PR_STALE",
                target=f"#{pull['number']}",
                argument=pull.get("headRefName", ""),
                evidence=f"{state} pull request untouched for {age}h: {pull.get('title', '')}",
                rule=RULE_STALE,
                recommendation="land it, close it, or say what it is waiting on; quiet is not a state",
            )
        )
    return actions


def build(root: Path, capture: dict[str, Any], stale_hours: int = STALE_HOURS) -> Batch:
    """Survey one capture into a reviewable batch of recommendations."""
    receipt = capture["receipt"]
    batch = Batch(
        repository=receipt["source_repository"],
        captured_at=receipt["captured_at"],
        export_digest=receipt["export_digest"],
    )
    batch.actions.extend(survey_catalogue(root, capture.get("labels", [])))
    batch.actions.extend(survey_tickets(root, capture["issues"]))
    batch.actions.extend(survey_branches(capture["pulls"], capture.get("branches", [])))
    batch.actions.extend(
        survey_pulls(capture["pulls"], _parse_time(receipt["captured_at"]), stale_hours)
    )
    return batch
