"""What a check is, and where the tree it runs against starts.

Held apart so `checks.py` and `participants.py` can each declare their half of the
table without one importing the other, and so a reader looking for the shape of an
entry finds one file rather than guessing which half defines it.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[2]

#: The two gates `scripts/verify.py --gate` accepts. `MAIN_GATE` is every check
#: the table holds, unchanged from what a run executes today. `DEV_GATE` is the
#: subset that can only fail because behaviour is wrong: a check whose failure
#: mode is a stale derived page, a stale counted claim, a stale receipt, a stale
#: witness record, or governing prose that has drifted from the tree stays out.
MAIN_GATE = "main"
DEV_GATE = "dev"


class Check(NamedTuple):
    name: str
    command: list[str]
    cwd: Path
    relation: str
    observes: tuple[str, ...]
    #: Which gate this check belongs to. Defaults to the main gate, so an entry
    #: that names nothing keeps running exactly where it runs today.
    gate: str = MAIN_GATE
