"""A prepared, empty journal these tests copy instead of creating one each.

`RecordService` creates SQLite schema on first open. That costs about 37 ms here
and far more on a small CI runner under load; copying a prepared empty store costs
about 3.5 ms, and the result is byte-identical to a fresh one - same schema, no
records - so a case that needs a virgin journal still gets one.

The reason to care is not this suite's own wall time. `scripts/verify.py` runs 39
checks concurrently, so what any check spends is taken from every other check in
the pool. On a two-core runner the pool is oversubscribed and every check's wall
time inflates together, which is how a suite that grew by three seconds of work
pushed an unrelated, byte-identical check from 4.6 s to 18.0 s and failed the gate.

Not a test module: `unittest discover` matches `test*.py`, so this is never
collected as one.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import atexit
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "record" / "src"))

from soveraeign_record_service import RecordService  # noqa: E402

_PREPARED: dict[str, Path] = {}


def _prepared() -> Path:
    """The empty journal, created on first use and removed when the process exits."""
    if not _PREPARED:
        holder = TemporaryDirectory(ignore_cleanup_errors=True)
        atexit.register(holder.cleanup)
        journal = Path(holder.name) / "journal"
        RecordService(journal).close()
        _PREPARED["journal"] = journal
    return _PREPARED["journal"]


def empty_journal(path: Path) -> Path:
    """A private, empty journal at ``path``, isolated from every other case."""
    shutil.copytree(_prepared(), path)
    return path
