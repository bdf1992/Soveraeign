#!/usr/bin/env python3
"""File an agent's stall as an unblock request draft.

Blocked is never a status: an agent that cannot advance names the exact
transition, the missing precondition, and the provision it asks a tier for,
and this script writes that claim as a schema-valid ticket draft under
``.claude/drafts/unblocks/``. Posting the draft as a live issue is an external
coordination action this local drafter does not perform; it requires the separate
attended/scoped crossing that owns GitHub writes. The draft is the record-local
half the agent may always take.

``draft`` refuses an invalid claim the same way the registrar would, so a
stall that cannot prove itself (``AGENTS.md``, Blocked edge is not blocked
frontier) never becomes a queued request. ``list`` renders the pending drafts
as the typed queue they will become.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import validate  # noqa: E402

DRAFTS = ROOT / ".claude" / "drafts" / "unblocks"
SCHEMA = ROOT / "contracts" / "issue-metadata.schema.json"

FIELDS = (
    ("held", "issue ref that cannot advance, e.g. #41"),
    ("village", "village enum value of the held ticket"),
    ("village-issue", "issue ref of that village"),
    ("parent", "issue ref the request reports under"),
    ("blocked-transition", "the exact unavailable transition"),
    ("missing-precondition", "what the transition checks and does not find"),
    ("governing-rule", "document and section that makes it binding"),
    ("provision", "grant | judgement | contract | fixture | capability | observation"),
    ("requested-by", "tier that hit the wall: worker | orchestrator | controller | owner"),
    ("requested-from", "tier asked to serve"),
    ("unblock-condition", "the observable condition a receipt will settle"),
)


def _slug(text: str) -> str:
    kept = [c if c.isalnum() else "-" for c in text.upper()]
    out = "".join(kept)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


def _metadata(args: argparse.Namespace) -> dict[str, object]:
    return {
        "issue_schema": "soveraeign-ticket/v1",
        "tags": [
            "kind:unblock",
            f"village:{args.village}",
            "horizon:now",
            "effect:request-only",
        ],
        "kind": "unblock",
        "unblock_id": f"UNBLOCK-{_slug(args.blocked_transition)}",
        "held": args.held,
        "village": args.village,
        "village_issue": args.village_issue,
        "parent": args.parent,
        "blocked_transition": args.blocked_transition,
        "missing_precondition": args.missing_precondition,
        "governing_rule": args.governing_rule,
        "requested_provision": args.provision,
        "requested_by": args.requested_by,
        "requested_from": args.requested_from,
        "unblock_condition": args.unblock_condition,
        "reachable_alternative": "NONE",
        "standing": "PROPOSED",
        "horizon": "NOW",
        "authority": f"{args.requested_by}: request only; no grant widened",
        "effect_class": "REQUEST_ONLY",
        "evidence_pointer": args.evidence,
        "last_observed_at": None,
        "walker_receipt": "unfiled-draft",
        "demotion_pointer": args.parent,
        "dependency_channels": [],
    }


def _render(metadata: dict[str, object]) -> str:
    lines = [f"# {metadata['unblock_id']} — unblock {metadata['held']}", "", "```yaml"]
    for key, value in metadata.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f'  - "{item}"' for item in value)
        elif value is None:
            lines.append(f"{key}: null")
        else:
            lines.append(f"{key}: {json.dumps(value) if ' ' in str(value) or ':' in str(value) else value}")
    lines.append("```")
    lines.append("")
    lines.append(
        f"Filed by the {metadata['requested_by']} tier for the "
        f"{metadata['requested_from']} tier. The held ticket adds this issue to its "
        "`requires` when the draft is posted. Reachable alternative: NONE is a claim; "
        "a witness who finds one closes this draft as refused."
    )
    return "\n".join(lines) + "\n"


def command_draft(args: argparse.Namespace) -> int:
    """Validate the claim and write the draft, refusing an unprovable stall."""
    metadata = _metadata(args)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    defects = validate(metadata, schema)
    if defects:
        for defect in defects:
            print(f"REFUSED: {defect}")
        return 1
    DRAFTS.mkdir(parents=True, exist_ok=True)
    path = DRAFTS / f"{metadata['unblock_id'].lower()}.md"
    if path.exists() and not args.force:
        shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        print(f"REFUSED: {shown} already exists; pass --force to replace it")
        return 1
    path.write_text(_render(metadata), encoding="utf-8", newline="\n")
    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    print(f"DRAFTED: {shown}")
    print(f"  holds {metadata['held']} on {metadata['blocked_transition']}; "
          f"asks {metadata['requested_from']} for a {metadata['requested_provision']}")
    print("  posting it is a separate attended/scoped external coordination action")
    return 0


def command_list(_: argparse.Namespace) -> int:
    """Render the pending drafts as the typed queue they will become."""
    drafts = sorted(DRAFTS.glob("*.md")) if DRAFTS.is_dir() else []
    if not drafts:
        print("no unblock drafts pending")
        return 0
    from sovticket.yamlblock import load_ticket  # noqa: PLC0415

    for path in drafts:
        metadata = load_ticket(path.read_text(encoding="utf-8"))
        print(f"{path.stem}: holds {metadata.get('held')} on {metadata.get('blocked_transition')}; "
              f"{metadata.get('requested_provision')} from {metadata.get('requested_from')}")
    print(f"\n{len(drafts)} pending; projection only, grants nothing.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sov_unblock", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    draft = sub.add_parser("draft", help="validate and write one unblock request draft")
    for name, help_text in FIELDS:
        draft.add_argument(f"--{name}", required=True, help=help_text,
                           dest=name.replace("-", "_"))
    draft.add_argument("--evidence", default="filed by sov_unblock.py",
                       help="evidence pointer for the claim")
    draft.add_argument("--force", action="store_true", help="replace an existing draft")
    draft.set_defaults(func=command_draft)
    listing = sub.add_parser("list", help="show pending unblock drafts")
    listing.set_defaults(func=command_list)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
