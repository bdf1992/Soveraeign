from __future__ import annotations

from pathlib import Path


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected repair block not found in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


test_path = Path("services/asset/tests/test_operational_record.py")
replace(
    test_path,
    '''            self.assertEqual(asset.history(result["asset_id"])[0]["version_id"],
                             result["version_id"])
''',
    '''            self.assertEqual(asset.history(result["asset_id"])[0]["id"],
                             result["version_id"])
''',
)

# Keep the Record protocol at the Store/operational seam rather than spending
# Asset core's last lines on a dependency type it never calls directly.
core_path = Path("services/asset/src/soveraeign_asset_service/core.py")
replace(
    core_path,
    "from soveraeign_asset_service.operational import OperationalJournal\n",
    "",
)
replace(
    core_path,
    '''    def __init__(self, root: str | Path, clock: Callable[[], float] = time.time,
                 operational_record: OperationalJournal | None = None):
''',
    '''    def __init__(self, root: str | Path, clock: Callable[[], float] = time.time,
                 operational_record: Any = None):
''',
)
replace(
    core_path,
    '''The SQLite database remains the canonical domain ledger for this slice; the
search and graph tables are disposable projections. When the declared Record port
is bound, each terminal receipt is durably outboxed with that local transaction and
mirrored into Record as operational history. Record does not become authority over
Asset rows by receiving that history.
''',
    '''The SQLite database remains the canonical domain ledger; search and graph tables
are projections. Terminal receipts cross a bound Record port as operational history;
Record does not become authority over Asset rows by receiving that history.
''',
)
