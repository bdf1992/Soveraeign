#!/usr/bin/env python3
"""Walk one measured execution up to the product intention that justified it.

`GROUND-014` says effort resolves to intention: any meaningful expenditure of time,
tokens, tools or money can be traced up to what justified it, and any product intention
can be traced down to what has been spent realizing it. This walks the first direction,
from a receipt that recorded what it served and what it spent.

    receipt -> capability -> operation -> journey -> promise -> ground

Usage is measured once and viewed through every intention that contains it. The views
overlap on purpose - one run really does serve several promises - and summing them would
report a node spending several times what it spent, so the measured total is computed
from the distinct receipts and never from a view
(`scripts/sovkernel/attribution.py`).

A work item is joined in when the receipt's capability appears in a ticket's `capability`
referent. That referent points at what the repository already names; it never carries a
second definition of it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import attribution  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402

CANON_PATH = ROOT / "contracts" / "product-canon.json"
GROUND_PATH = ROOT / "contracts" / "product-ground.json"
MAP_PATH = ROOT / "contracts" / "fixtures" / "capability-map.reference.json"
RECEIPT_SCHEMA = ROOT / "contracts" / "receipt.schema.json"
DEFAULT_RECEIPT = ROOT / "bindings" / "mcp" / "observations" / "journey-02-receipt.json"


def _load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def units(receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One usage record per receipt that recorded what it served and what it spent.

    A receipt with no `consumed` block measured nothing and is left out rather than
    entered as a zero, because a zero is a measurement and an absence is not.
    """
    return [{"unit_id": receipt["receipt_id"],
             "directly_serves": receipt["serves_capability"],
             "consumed": {entry["dimension"]: entry["amount"]
                          for entry in receipt["consumed"]}}
            for receipt in receipts
            if receipt.get("serves_capability") and receipt.get("consumed")]


def tickets(payload: Any) -> list[dict[str, Any]]:
    """Ticket metadata from either a plain array or a conformance case corpus.

    Reading the corpus directly means the join is demonstrated against fixtures the
    repository already checks, rather than against an example written to agree with it.
    """
    if isinstance(payload, dict) and "cases" in payload:
        return [case["metadata"] for case in payload["cases"]
                if case.get("expect") == "VALID"]
    return list(payload)


def _work_items(capability_id: str, items: list[dict[str, Any]]) -> list[str]:
    return [item.get("engagement_id") or item.get("bit_id") or item.get("epic_id")
            or "<unnamed>"
            for item in items if capability_id in item.get("capability", [])]


def command_up(args: argparse.Namespace) -> int:
    """From a receipt, upward to the ground claim that justified the spend."""
    receipts = [_load(Path(path)) for path in (args.receipts or [DEFAULT_RECEIPT])]
    schema = _load(RECEIPT_SCHEMA)
    defects = [f"{receipt.get('receipt_id', '<unnamed>')}: {defect}"
               for receipt in receipts for defect in validate(receipt, schema)]
    if defects:
        for defect in defects:
            print(f"CONTRACT: {defect}")
        print(f"\nFAIL: {len(defects)} receipt defect(s)")
        return 1

    canon = _load(CANON_PATH)
    ground = {claim["ground_id"]: claim for claim in _load(GROUND_PATH)["claims"]}
    rows = {row["capability_id"]: row for row in _load(MAP_PATH)["capabilities"]}
    items = tickets(_load(Path(args.tickets))) if args.tickets else []
    measured = attribution.rollup(canon, units(receipts))

    for receipt in receipts:
        capability_id = receipt.get("serves_capability")
        print(f"\n{receipt['receipt_id']}  {receipt['outcome']}  "
              f"{receipt['created_at']}")
        print(f"  through   {receipt['interface_id']}")
        if not capability_id:
            print("  serves    nothing declared; this receipt cannot resolve upward")
            continue
        spent = ", ".join(f"{entry['amount']:g} {entry['dimension']}"
                          for entry in receipt.get("consumed", [])) or "nothing measured"
        print(f"  spent     {spent}")
        row = rows.get(capability_id, {})
        shape = row.get("shape", {})
        ancestors = attribution.capability_ancestors(canon, capability_id)
        served_by = _work_items(capability_id, items)
        print(f"\n  CAPABILITY  {capability_id}  [{row.get('service_standing', '?')}]")
        print(f"  OPERATION   {shape.get('logical_endpoint', '?')}  "
              f"requires {row.get('required_authority', '?')}  "
              f"{row.get('effect_class', '?')}")
        print(f"  REQUIREMENT {shape.get('requirement', 'none declared')}")
        print(f"  WORK ITEM   "
              f"{', '.join(served_by) if served_by else 'none names this capability'}")
        print(f"  JOURNEY     {', '.join(ancestors['journey']) or 'none'}")
        print(f"  PROMISE     {', '.join(ancestors['promise']) or 'none'}")
        for claim_id in ancestors["ground"]:
            print(f"  GROUND      {claim_id}  "
                  f"{ground[claim_id]['statement'].split('.')[0][:70]}")

    print(f"\nMEASURED ONCE across {measured['unit_count']} receipt(s): "
          + ", ".join(f"{amount:g} {dimension}"
                      for dimension, amount in sorted(measured["measured"].items())))
    for level in attribution.LEVELS:
        gap = attribution.overlap(measured, level)
        invented = ", ".join(f"{value:g} {dimension}"
                             for dimension, value in sorted(gap.items()) if value)
        print(f"  summing the {level} views would invent {invented or 'nothing'}")
    print("Every view above is a true reading of the same expenditure. The expenditure "
          "happened once.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sov_trace", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    up = sub.add_parser("up", help="from a measured receipt to the intention behind it")
    up.add_argument("receipts", nargs="*",
                    help=f"receipt files (default {DEFAULT_RECEIPT.name})")
    up.add_argument("--tickets", default=None,
                    help="a JSON array of ticket metadata, to join work items in")
    up.set_defaults(handler=command_up)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
