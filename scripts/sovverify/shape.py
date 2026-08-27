"""What a check is, and where the tree it runs against starts.

Held apart so `checks.py` and `participants.py` can each declare their half of the
table without one importing the other, and so a reader looking for the shape of an
entry finds one file rather than guessing which half defines it.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[2]


class Check(NamedTuple):
    name: str
    command: list[str]
    cwd: Path
    relation: str
    observes: tuple[str, ...]
