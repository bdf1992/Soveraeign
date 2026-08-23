#!/usr/bin/env python3
"""Board management command line: survey the coordination surface, then apply what is approved.

The split is deliberate. ``review`` reads, judges, and recommends; it never writes. ``apply``
holds no GitHub knowledge at all and hands an approved action list to the declared write
crossing under ``adapters/github/apply.py`` as a separate process, so the only module that
can write to GitHub stays the only module that can write to GitHub.

The surface this prints is the point of the tool. A recommendation without its evidence
asks the reader to redo the survey before they can approve it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovboard import render as rendermod  # noqa: E402
from sovboard import survey as surveymod  # noqa: E402
from sovboard.actions import Batch, load_batch, select  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REGISTRAR = ROOT / "adapters" / "github" / "export.py"
CROSSING = ROOT / "adapters" / "github" / "apply.py"
FIXTURES = ROOT / "conformance" / "fixtures" / "board"
DEFAULT_DIR = ROOT / ".local" / "board"


def _default_repo() -> str | None:
    """Read ``owner/name`` from the local git remote; no network is involved."""
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=False, cwd=ROOT
    )
    if result.returncode:
        return None
    url = result.stdout.strip().removesuffix(".git")
    parts = url.replace(":", "/").split("/")
    return "/".join(parts[-2:]) if len(parts) >= 2 else None


def _capture(repo: str, export: Path) -> None:
    """Run the read registrar, letting its own refusals reach the operator unchanged."""
    result = subprocess.run(
        [sys.executable, str(REGISTRAR), "--repo", repo, "--out", str(export)],
        text=True, check=False, cwd=ROOT,
    )
    if result.returncode:
        raise SystemExit("REFUSED: the registrar could not capture the coordination surface")


#: The sidecar files one capture writes, keyed by the survey input each one feeds.
#: Every one is required. A missing sidecar reads as an empty collection, and an empty
#: collection is not "nothing to do" — an empty label catalogue makes every declared
#: label look absent, and an empty branch list makes every merged ref look pruned.
SIDECARS = {"pulls": ".pulls.json", "branches": ".branches.json", "labels": ".labels.json"}


def _load_capture(export: Path) -> dict[str, Any]:
    """Load every file one capture writes, refusing a partial capture rather than
    surveying against a silently empty collection."""
    paths = {"receipt": export.with_name(export.stem + ".receipt.json")}
    for key, suffix in SIDECARS.items():
        paths[key] = export.with_name(export.stem + suffix)
    missing = [path.name for path in [export, *paths.values()] if not path.exists()]
    if missing:
        raise SystemExit(
            f"REFUSED [CAPTURE_INCOMPLETE]: missing {', '.join(missing)}; "
            "re-run review without --export to take a fresh capture"
        )
    capture = {"issues": json.loads(export.read_text(encoding="utf-8"))}
    for key, path in paths.items():
        capture[key] = json.loads(path.read_text(encoding="utf-8"))
    return capture


def command_review(args: argparse.Namespace) -> int:
    """Survey the coordination surface into a reviewable batch of recommendations."""
    export = Path(args.export) if args.export else DEFAULT_DIR / "tickets.json"
    if not args.export:
        repo = args.repo or _default_repo()
        if repo is None:
            raise SystemExit("REFUSED: no --repo given and no git remote to read one from")
        export.parent.mkdir(parents=True, exist_ok=True)
        _capture(repo, export)
    batch = surveymod.build(ROOT, _load_capture(export), args.stale_hours)
    out = Path(args.out) if args.out else DEFAULT_DIR / "batch.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(batch.dumps(), encoding="utf-8", newline="\n")
    if args.json:
        print(batch.dumps(), end="")
    else:
        print(rendermod.render(batch, str(out)))
    return 0


def _approved_actions(batch: Batch, tokens: list[str]) -> list[dict[str, Any]]:
    """Resolve approval tokens into executable actions, refusing anything unapprovable."""
    approved, refusals = select(batch, tokens)
    for refusal in refusals:
        print(f"REFUSED: {refusal}", file=sys.stderr)
    if refusals:
        raise SystemExit("REFUSED [UNAPPROVABLE]: no action was applied; correct the approval and retry")
    if not approved:
        raise SystemExit("REFUSED [NO_APPROVAL]: the approval selected nothing executable")
    return [action.as_dict() for action in approved]


def command_apply(args: argparse.Namespace) -> int:
    """Apply the approved subset of a batch through the declared write crossing."""
    batch_path = Path(args.batch)
    batch = load_batch(json.loads(batch_path.read_text(encoding="utf-8")))
    tokens = [token.strip() for token in args.approve.split(",") if token.strip()]
    actions = _approved_actions(batch, tokens)
    approved_path = batch_path.with_name(batch_path.stem + ".approved.json")
    approved_path.write_text(json.dumps(actions, indent=2) + "\n", encoding="utf-8", newline="\n")
    receipts_path = batch_path.with_name(batch_path.stem + ".receipts.json")
    print(
        f"Approved {len(actions)} of {len(batch.proposed)} proposed action(s) on {batch.repository}.",
        flush=True,
    )
    command = [
        sys.executable, str(CROSSING), "--repo", batch.repository,
        "--actions", str(approved_path), "--receipts", str(receipts_path),
    ]
    if args.dry_run:
        command.append("--dry-run")
    return subprocess.run(command, text=True, check=False, cwd=ROOT).returncode


def command_selfcheck(_: argparse.Namespace) -> int:
    """Run the declared positive and defeating board fixtures without a network."""
    cases = json.loads((FIXTURES / "survey-cases.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    for case in cases["cases"]:
        batch = surveymod.build(ROOT, case["capture"])
        observed = sorted(f"{action.kind}:{action.target}:{action.argument}" for action in batch.actions)
        expected = sorted(case["expect_actions"])
        if observed != expected:
            failures.append(f"{case['case_id']}: expected {expected}, observed {observed}")
    for case in cases["approval_cases"]:
        batch = load_batch(case["batch"])
        _, refusals = select(batch, case["approve"])
        wanted = case.get("refuses")
        if wanted and not any(wanted in refusal for refusal in refusals):
            failures.append(f"{case['case_id']}: expected a refusal naming {wanted!r}, observed {refusals}")
        if not wanted and refusals:
            failures.append(f"{case['case_id']}: expected no refusal, observed {refusals}")
    for failure in failures:
        print(f"FAIL: {failure}")
    total = len(cases["cases"]) + len(cases["approval_cases"])
    if failures:
        print(f"\nFAIL: {len(failures)} of {total} board fixture cases")
        return 1
    defeating = sum(1 for case in cases["approval_cases"] if case.get("refuses"))
    defeating += sum(1 for case in cases["cases"] if case.get("defeating"))
    print(f"PASS: {total} board fixture cases ({total - defeating} positive, {defeating} defeating)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for every board subcommand."""
    parser = argparse.ArgumentParser(prog="sov_board", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    review = subparsers.add_parser("review", help=command_review.__doc__)
    review.set_defaults(handler=command_review)
    review.add_argument("--repo", help="owner/name; defaults to the origin remote")
    review.add_argument("--export", help="judge an existing capture instead of taking a new one")
    review.add_argument("--out", help="path for the batch (default .local/board/batch.json)")
    review.add_argument("--json", action="store_true", help="print the batch instead of the surface")
    review.add_argument(
        "--stale-hours", type=int, default=surveymod.STALE_HOURS,
        help=f"hours of silence before a pull request is reported (default {surveymod.STALE_HOURS})",
    )

    apply_cmd = subparsers.add_parser("apply", help=command_apply.__doc__)
    apply_cmd.set_defaults(handler=command_apply)
    apply_cmd.add_argument("--batch", required=True, help="batch produced by review")
    apply_cmd.add_argument("--approve", required=True, help="comma-separated action ids, or 'all'")
    apply_cmd.add_argument("--dry-run", action="store_true", help="print the exact commands only")

    selfcheck = subparsers.add_parser("selfcheck", help=command_selfcheck.__doc__)
    selfcheck.set_defaults(handler=command_selfcheck)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch one subcommand."""
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
