"""Asset identity over time, and the two kinds of sameness that are not identity.

`CLASSIFICATION.md` defines an Asset as a governed enterprise identity with a
version history, and an Asset version as an immutable state of that asset.
Identity therefore has to survive re-capture: capturing the same source twice is
one asset with two versions, never two assets.

Two other kinds of sameness are deliberately not identity, and neither is a kind
of asset:

- the same bytes reached through two different sources. The content store holds
  one blob and the two assets are genuinely distinct identities that happen to
  share custody of it. `duplicates` reads that fact off the store; nothing
  asserts it, so nothing can assert it wrongly.
- the same source captured again with unchanged bytes. That is not a new state
  of the asset, so it earns no version. The attempt is still receipted, because
  a caller that asked deserves an answer either way.

Composition is not modelled here. An asset assembled from others is derivation
with more than one input (`runs.py`), not a fifth kind of asset.
"""

from __future__ import annotations

from typing import Any
import sqlite3


ORIGINAL = "ORIGINAL"
REVISION = "REVISION"
DERIVATIVE = "DERIVATIVE"

CAPTURE_ROLES = (ORIGINAL, REVISION)


class Identity:
    """Resolves which asset a captured source belongs to, and reads sameness back out."""

    def __init__(self, db: sqlite3.Connection) -> None:
        self.db = db

    def by_locator(self, locator: str) -> sqlite3.Row | None:
        """The newest captured version reached through this locator, if the node has one.

        Identity follows the locator rather than the bytes: a document rewritten
        in place is the same asset, and two documents with identical bytes are
        not.
        """
        return self.db.execute(
            "SELECT v.id AS version_id, v.asset_id, v.digest, v.role, v.created_at, "
            "       s.id AS source_id, s.locator "
            "FROM versions v JOIN sources s ON v.source_id = s.id "
            "WHERE s.locator = ? AND v.role IN (?, ?) "
            "ORDER BY v.created_at DESC, v.id DESC LIMIT 1",
            (locator, ORIGINAL, REVISION),
        ).fetchone()

    def history(self, asset_id: str) -> list[dict[str, Any]]:
        """Every version of one asset, oldest first, with how each came to exist."""
        rows = self.db.execute(
            "SELECT id, asset_id, source_id, digest, mime, size, role, derivation_json, "
            "       created_at FROM versions WHERE asset_id = ? "
            "ORDER BY created_at, id", (asset_id,)).fetchall()
        return [dict(row) for row in rows]

    def duplicates(self) -> list[dict[str, Any]]:
        """Distinct assets whose newest versions share one payload digest.

        Derived, never asserted: it is read off the content store, so it cannot
        disagree with the store it describes. An entry here is not a defect - two
        identities may legitimately hold the same bytes - it is a fact an
        operator should be able to see.
        """
        rows = self.db.execute(
            "SELECT v.digest AS digest, GROUP_CONCAT(v.asset_id) AS assets, "
            "       COUNT(*) AS holders "
            "FROM versions v "
            "WHERE v.role IN (?, ?) AND v.id = ("
            "  SELECT n.id FROM versions n "
            "  WHERE n.asset_id = v.asset_id AND n.role IN (?, ?) "
            "  ORDER BY n.created_at DESC, n.id DESC LIMIT 1) "
            "GROUP BY v.digest HAVING holders > 1 ORDER BY v.digest",
            CAPTURE_ROLES + CAPTURE_ROLES,
        ).fetchall()
        return [{"digest": row["digest"], "asset_ids": sorted(row["assets"].split(",")),
                 "holders": row["holders"]} for row in rows]

    def relationships(self, asset_id: str) -> list[dict[str, Any]]:
        """Asserted relations touching this asset, in either direction, with their standing."""
        rows = self.db.execute(
            "SELECT id, src_asset, predicate, dst_asset, proposal_id, standing "
            "FROM relationships WHERE src_asset = ? OR dst_asset = ? "
            "ORDER BY predicate, dst_asset", (asset_id, asset_id)).fetchall()
        return [dict(row) for row in rows]
