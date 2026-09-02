"""Load the finding-comparison classification vocabulary at import time.

The vocabulary is declared in ``contracts/finding-comparison.json`` as the
canonical projection of the classification codes named in
``.claude/workflows/sov-loop.js`` and ``.claude/agents/sov-controller.md``.
"""

from __future__ import annotations

from pathlib import Path
import json

_CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contracts" / "finding-comparison.json"

with _CONTRACT_PATH.open("r", encoding="utf-8") as _f:
    _CONTRACT = json.load(_f)

CLASSIFICATIONS = _CONTRACT["classifications"]
