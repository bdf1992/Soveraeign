"""The Asset Service's read surface: every call that answers without writing.

Each method here delegates to the component that owns the state it reports on.
None of them commits, writes a receipt, or changes standing, and that is the line
the split follows: `core.py` keeps authority and the lifecycle transitions, which
write, and this keeps the questions you can ask about them, which do not.

`rebuild_projections` deliberately stays in `core.py` even though it sits under
the same heading there. It drops both views, derives them again and writes a
receipt, so it belongs with the writers no matter what it is named.

Split out when `core.py` reached the 300-line module limit. The alternative was
to shorten a docstring until the file fitted, which would have left the next
addition in the same position with less explanation of why.
"""

from __future__ import annotations

from typing import Any


class ReadSurface:
    """Read-only delegations, mixed into ``AssetService``.

    The attributes used here - ``projections``, ``identity``, ``store``,
    ``librarian`` - are established by ``AssetService.__init__``. This class is
    never instantiated on its own; it exists to keep the reads separable from the
    transitions rather than to be a component in its own right.
    """

    def projection_drift(self) -> list[dict[str, Any]]:
        """Every projected row that disagrees with the ledger. Writes nothing.

        The non-destructive half of ``rebuild_projections``: it answers whether a
        view matches what the ledger implies, without rebuilding, which would
        answer by destroying what it was asked about.

        It grades the view against the ledger and nothing else. It does not
        establish that the view is trustworthy, and an earlier version of this
        sentence said it did. A row forged straight into the `assets` table
        derives cleanly and is reported as no drift, and a claim retracted by
        counter-record stays projected because the derivation does not read
        retractions - both are agreements between the view and the ledger about
        something the ledger should not be carrying.
        """
        return self.projections.drift()

    def history(self, asset_id: str) -> list[dict[str, Any]]:
        """Every version of one asset, oldest first."""
        return self.identity.history(asset_id)

    def duplicates(self) -> list[dict[str, Any]]:
        """Distinct assets whose newest versions share one payload digest."""
        return self.identity.duplicates()

    def relationships(self, asset_id: str) -> list[dict[str, Any]]:
        """Asserted relations touching this asset, in either direction."""
        return self.identity.relationships(asset_id)

    def search(self, query: str) -> list[str]:
        """Assets whose projected text contains the query."""
        return self.projections.search(query)

    def neighbors(self, asset_id: str) -> list[dict[str, Any]]:
        """Projected edges touching an asset."""
        return self.projections.neighbors(asset_id)

    def receipts(self) -> list[dict[str, Any]]:
        """Every receipt in write order."""
        return self.store.receipts()

    def library_report(self) -> dict[str, Any]:
        """Every collection judged against its type, plus the assets nobody filed."""
        return self.librarian.report()


__all__ = ["ReadSurface"]
