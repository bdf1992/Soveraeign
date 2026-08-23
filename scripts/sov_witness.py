#!/usr/bin/env python3
"""Perform the semantic task a fresh witness can judge without reading the code.

`OPEN-SEAMS.md` S5 and open decision O8 say the same thing: structural
completeness and schema validity are measurable and do not establish semantic
competence, and Phase I needs a watched task whose success a fresh witness can
determine independently. Until this existed, `PROD-I-7` could not be satisfied
honestly, and `SPEC.md` could not reach `WITNESSED`.

The task is a custody round trip under mutation. The witness supplies bytes the
repository has never seen, and judges the result by comparing digests it
computed itself. No part of the verdict requires reading an implementation,
trusting a receipt's wording, or validating a schema: either the exact bytes come
back, or they do not; either the system refuses a changed source, or it does not.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
import argparse
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "asset" / "src"))

from soveraeign_asset_service.core import AssetService  # noqa: E402
from soveraeign_asset_service.custody import (  # noqa: E402
    SourceChanged,
    read_version,
    reread_source,
)


def _witness_bytes(seed: str) -> bytes:
    """Bytes derived from a witness-chosen seed, so the corpus has never held them."""
    material = sha256(f"witness:{seed}".encode("utf-8")).digest()
    return b"SOVERAEIGN WITNESS PAYLOAD\n" + material * 8


def run_task(seed: str) -> dict[str, Any]:
    """Run the custody round trip under mutation and report what was observed."""
    started = time.perf_counter()
    supplied = _witness_bytes(seed)
    supplied_digest = sha256(supplied).hexdigest()
    checks: list[dict[str, Any]] = []

    def record(name: str, held: bool, detail: str) -> None:
        checks.append({"check": name, "held": held, "detail": detail})

    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        source = root / "witness-payload.bin"
        source.write_bytes(supplied)
        service = AssetService(root / "state")
        try:
            ingested = service.ingest(source, "Witness payload", "witness")

            returned = read_version(service, ingested["version_id"], "witness")
            returned_digest = sha256(returned["bytes"]).hexdigest()
            record(
                "bytes_return_identical",
                returned["bytes"] == supplied and returned_digest == supplied_digest,
                f"supplied {supplied_digest[:16]}, returned {returned_digest[:16]}",
            )
            record(
                "version_resolves_its_source",
                returned["source_id"] == ingested["source_id"],
                f"version resolves source {returned['source_id']}",
            )

            unchanged = reread_source(service, ingested["source_id"], "witness")
            record(
                "unchanged_source_verifies",
                unchanged["digest"] == supplied_digest,
                "the source still matches the digest captured at ingest",
            )

            # The world moves underneath: the same path, different bytes.
            source.write_bytes(supplied + b"\nmutated by the witness\n")
            try:
                reread_source(service, ingested["source_id"], "witness")
                record("changed_source_refused", False,
                       "the system returned a reading for a source that had changed")
            except SourceChanged as refusal:
                record("changed_source_refused", True, str(refusal))

            # Custody is unaffected by the mutation: the held bytes are still the
            # bytes that were captured, which is what "remember" has to mean.
            after = read_version(service, ingested["version_id"], "witness")
            record(
                "custody_survives_source_mutation",
                after["bytes"] == supplied,
                "held bytes still equal the bytes supplied before the mutation",
            )

            reasons = [json.loads(r["payload_json"]).get("reason")
                       for r in service.db.execute(
                           "SELECT payload_json FROM receipts WHERE outcome='REFUSED'"
                       ).fetchall()]
            record(
                "refusal_is_receipted",
                "SOURCE_CHANGED" in reasons,
                f"refused receipts recorded: {[r for r in reasons if r]}",
            )
        finally:
            service.close()

    held = all(check["held"] for check in checks)
    return {
        "task_id": "SEMANTIC-CUSTODY-ROUND-TRIP",
        "seed": seed,
        "supplied_digest": supplied_digest,
        "checks": checks,
        "held": held,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }


def command_semantic(args: argparse.Namespace) -> int:
    """Run the task and print what a witness would be able to judge."""
    result = run_task(args.seed)
    for check in result["checks"]:
        mark = "HOLDS " if check["held"] else "FAILED"
        print(f"{mark} {check['check']}: {check['detail']}")
    print()
    if not result["held"]:
        failed = [c["check"] for c in result["checks"] if not c["held"]]
        print(f"FAIL: the semantic task did not hold: {', '.join(failed)}")
        return 1
    print(
        f"PASS: {len(result['checks'])} semantic checks held in "
        f"{result['elapsed_seconds']}s, judged by digests the witness computed"
    )
    if args.emit:
        Path(args.emit).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"observation written to {args.emit}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for every witness subcommand."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    semantic = sub.add_parser("semantic", help="run the semantic cold-start task")
    semantic.add_argument("--seed", default="default-witness",
                          help="witness-chosen seed for bytes the corpus has never held")
    semantic.add_argument("--emit", help="write the observation to this path")
    semantic.set_defaults(handler=command_semantic)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one witness subcommand."""
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
