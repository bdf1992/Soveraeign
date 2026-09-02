#!/usr/bin/env python3
"""Grade the Node Interface proof against P15-Q1.3: identity separation and refusal.

Runs the Human/Model proof, hands its ``identities`` block and its observed
``cross_principal_session_mismatch`` outcome to the independent commissioning
evaluator, and refuses if the evaluator finds a defect. This script does not
decide what a valid session or a valid grant is; ``sovnode.proof`` and the
Gateway it drives already do, and this only reads what they recorded.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from conformance import commissioning  # noqa: E402
from sovnode.proof import run as run_proof  # noqa: E402


def evaluate() -> list[str]:
    document = run_proof()
    observed = {
        "identities": document.get("identities"),
        "cross_principal_session_mismatch": document.get("cross_principal_session_mismatch"),
    }
    return commissioning.evaluate("P15-Q1.3", observed)


def main() -> int:
    defects = evaluate()
    if defects:
        print("FAIL: P15-Q1.3")
        for defect in defects:
            print(f"  {defect}")
        return 1
    print("PASS: P15-Q1.3 — identity separation holds and the mismatch refuses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
