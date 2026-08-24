#!/usr/bin/env python3
"""Apply the planned coordination writes to the GitHub surface.

The registrar's write half. Every action it performs was derived offline by ``plan.py``
from a local declaration, so the crossing carries no judgement of its own: it executes a
plan a fresh witness can regenerate from the export and the catalogue.

The crossing is ``COORDINATION_WRITE`` (``adapters/github/README.md``). It writes labels,
containment edges, and the rendered relations block, and nothing else. It never opens,
closes, comments on, assigns, or milestones an issue, and it never touches a body outside
the delimited block. Writing is opt-in: without ``--apply`` it prints the plan and stops.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import catalogue  # noqa: E402
import plan as planner  # noqa: E402
from export import RegistrarRefusal, _run, capture_parents  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OPERATIONS = ("labels", "issue-labels", "relations", "bodies")


def _now() -> str:
    """Return the current UTC instant in the receipt's timestamp form."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _gh(args: list[str]) -> str:
    """Run one gh invocation, converting failure into the registrar's declared refusal."""
    return _run(["gh", *args])


def _node_ids(repo: str) -> dict[int, str]:
    """Map issue number to GraphQL node id, for the sub-issue mutations."""
    rows = json.loads(_gh(["issue", "list", "--repo", repo, "--state", "all",
                           "--limit", "500", "--json", "number,id"]))
    return {int(row["number"]): row["id"] for row in rows}


def do_label(repo: str, action: catalogue.LabelAction) -> None:
    """Create, edit, or delete one label."""
    if action.verb == "delete":
        _gh(["label", "delete", action.name, "--repo", repo, "--yes"])
        return
    verb = "create" if action.verb == "create" else "edit"
    args = ["label", verb, action.name, "--repo", repo,
            "--color", action.color, "--description", action.description]
    if verb == "create":
        args.append("--force")
    _gh(args)


def do_issue_labels(repo: str, action: catalogue.IssueLabelAction) -> None:
    """Bring one issue's governed labels in line with its metadata."""
    ref = str(action.number)
    if action.add:
        _gh(["issue", "edit", ref, "--repo", repo,
             *[part for name in action.add for part in ("--add-label", name)]])
    if action.remove:
        _gh(["issue", "edit", ref, "--repo", repo,
             *[part for name in action.remove for part in ("--remove-label", name)]])


def do_relation(repo: str, action: planner.RelationAction, ids: dict[int, str]) -> None:
    """Attach one issue to its container as a native sub-issue."""
    missing = [number for number in (action.parent, action.child) if number not in ids]
    if missing:
        raise RegistrarRefusal("REGISTRAR_REFUSED", f"no node id for issue(s) {missing}")
    mutation = (
        "mutation($parent:ID!,$child:ID!){addSubIssue(input:{issueId:$parent,subIssueId:$child})"
        "{issue{number}}}"
    )
    _gh(["api", "graphql", "-f", f"query={mutation}",
         "-F", f"parent={ids[action.parent]}", "-F", f"child={ids[action.child]}"])


def do_body(repo: str, action: planner.BodyAction, scratch: Path) -> None:
    """Replace one issue body with its rewritten form, passing the text through a file.

    The body goes through a file rather than an argument: it is multi-line markdown, and
    a shell-quoted body is exactly where an issue's contract block gets mangled.
    """
    scratch.mkdir(parents=True, exist_ok=True)
    path = scratch / f"body-{action.number}.md"
    path.write_text(action.body, encoding="utf-8", newline="\n")
    _gh(["issue", "edit", str(action.number), "--repo", repo, "--body-file", str(path)])


def snapshot_bodies(bodies: dict[int, str], out: Path) -> Path:
    """Write every current body to disk before any of them is rewritten.

    A rewrite of 43 contract-bearing bodies needs a path back that does not depend on the
    tool that performed it. This is that path.
    """
    out.mkdir(parents=True, exist_ok=True)
    for number, body in sorted(bodies.items()):
        (out / f"body-{number}.md").write_text(body, encoding="utf-8", newline="\n")
    return out


def build_plan(export: Path) -> dict[str, list[Any]]:
    """Derive every planned action offline from the export and the local declarations."""
    governed, retired = catalogue.read_catalogue(ROOT)
    live_catalogue = catalogue.live_labels(export)
    metadata, bodies, titles, defects = planner.load_export(export)
    projection = catalogue.load_projection(ROOT)
    raw = json.loads(export.read_text(encoding="utf-8"))
    live_issue_labels = {
        int(issue["number"]): [label["name"] for label in issue.get("labels") or []]
        for issue in raw
    }
    issue_label_actions, unmapped = catalogue.plan_issue_labels(
        metadata, live_issue_labels, projection
    )
    return {
        "labels": catalogue.plan_labels(governed, retired, live_catalogue),
        "issue-labels": issue_label_actions,
        "relations": planner.containment_edges(metadata, planner.held_parents(export)),
        "bodies": planner.plan_bodies(metadata, bodies, titles),
        "_bodies_before": bodies,
        "_defects": defects + unmapped,
    }


def _performer(operation: str, repo: str, state: dict[str, Any]) -> Callable[[Any], None]:
    """Return the callable that performs one action of the named operation."""
    if operation == "labels":
        return lambda action: do_label(repo, action)
    if operation == "issue-labels":
        return lambda action: do_issue_labels(repo, action)
    if operation == "relations":
        return lambda action: do_relation(repo, action, state["ids"])
    return lambda action: do_body(repo, action, state["scratch"])


def run(repo: str, export: Path, operations: tuple[str, ...], apply: bool, out: Path) -> int:
    """Print the plan and, with ``apply``, perform it and write a receipt."""
    planned = build_plan(export)
    for defect in planned["_defects"]:
        print(f"SKIPPED {defect}")

    total = sum(len(planned[name]) for name in operations)
    for name in operations:
        actions = planned[name]
        print(f"\n{name}: {len(actions)} action(s)")
        for action in actions:
            print(f"  {action.describe()}")
    if not apply:
        print(f"\nPLAN ONLY: {total} action(s) not performed. Re-run with --apply to cross.")
        return 0
    if not total:
        print("\nNothing to apply; the surface already matches the declarations.")
        return 0

    out.mkdir(parents=True, exist_ok=True)
    state: dict[str, Any] = {"scratch": out / "bodies-after"}
    if "bodies" in operations:
        print(f"\nRollback snapshot: {snapshot_bodies(planned['_bodies_before'], out / 'bodies-before')}")
    if "relations" in operations:
        state["ids"] = _node_ids(repo)
        # The export can be minutes old; re-read the graph so a concurrently added edge
        # is not written twice.
        held = capture_parents(repo)
        planned["relations"] = [
            edge for edge in planned["relations"] if held.get(edge.child) != edge.parent
        ]
        print(f"relations: {len(planned['relations'])} action(s) against the live graph")

    performed: list[dict[str, Any]] = []
    started = _now()
    for name in operations:
        perform = _performer(name, repo, state)
        for action in planned[name]:
            record = {"operation": name, "action": action.describe()}
            try:
                perform(action)
                record["outcome"] = "APPLIED"
            except RegistrarRefusal as refusal:
                record["outcome"] = f"REFUSED [{refusal.code}]"
                record["detail"] = refusal.detail
            print(f"  {record['outcome']:<24} {record['action']}")
            performed.append(record)

    applied = sum(1 for record in performed if record["outcome"] == "APPLIED")
    receipt = {
        "registrar": "github-coordination/v1",
        "crossing": "COORDINATION_WRITE",
        "target_repository": repo,
        "started_at": started,
        "completed_at": _now(),
        "operations": list(operations),
        "planned": len(performed),
        "applied": applied,
        "refused": len(performed) - applied,
        "source_export": str(export),
        "effect_class": "EXTERNAL_WORLD",
        "authority": "Bdo, this session, for the label and containment surface only",
        "actions": performed,
        "note": "A write is an effect, not a judgement. Nothing here settles standing.",
    }
    receipt_path = out / "apply.receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"\nAPPLIED {applied}/{len(performed)}; receipt {receipt_path}")
    return 0 if applied == len(performed) else 1


def main(argv: list[str] | None = None) -> int:
    """Plan and optionally perform the coordination writes for one repository."""
    parser = argparse.ArgumentParser(prog="github-registrar-apply", description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/name of the coordination repository")
    parser.add_argument("--export", required=True, type=Path, help="the registrar export to plan from")
    parser.add_argument("--only", action="append", choices=OPERATIONS,
                        help="restrict to one operation; repeatable")
    parser.add_argument("--apply", action="store_true", help="perform the plan instead of printing it")
    parser.add_argument("--out", type=Path, default=Path(".local/registrar"),
                        help="directory for the receipt and the rollback snapshot")
    args = parser.parse_args(argv)
    operations = tuple(args.only) if args.only else OPERATIONS
    try:
        return run(args.repo, args.export, operations, args.apply, args.out)
    except (RegistrarRefusal, FileNotFoundError, ValueError) as error:
        code = getattr(error, "code", "REGISTRAR_REFUSED")
        print(f"REFUSED [{code}]: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
