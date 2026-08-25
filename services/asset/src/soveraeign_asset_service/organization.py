"""Typed collections over assets: the organizational layer an operator works in.

An **asset collection** is a named, typed, curated set of assets. Its type is a
declared schema - which metadata fields a member must carry, which values those
fields may take, and which asset roles the collection admits - so membership can
be judged rather than merely asserted. `librarian.py` does the judging.

Two names that are close and must not merge:

- `CLASSIFICATION.md` gives the Asset Projection Service a *projection
  collection*: a declared retrieval scope, which is an index. It is derived,
  rebuildable, and about lookup.
- The record here is a *curated* set. Someone decided each member belongs, and
  that decision is receipted and counter-recorded, never recomputed.

Every machine surface therefore says `asset-collection`, and prose qualifies the
bare word. The collision is recorded in `OPEN-SEAMS.md`.

Standing: declaring a type or a collection, and filing an asset into one, are
curatorial acts under a live grant. They are not judgement, so they do not pass
through `ratify`. What a member claims about itself still does: conformance
reads ratified descriptions, and an unratified one is reported as a claim rather
than counted as a fact (`decisions/0057-asset-collections-and-the-librarian.md`).
"""

from __future__ import annotations

from typing import Any
import json
import sqlite3

from soveraeign_asset_service.authority import Authority
from soveraeign_asset_service.identity import DERIVATIVE, ORIGINAL, REVISION
from soveraeign_asset_service.store import Store, new_id


SCHEMA = """
CREATE TABLE IF NOT EXISTS collection_types(
  id TEXT PRIMARY KEY, label TEXT NOT NULL, spec_json TEXT NOT NULL,
  declared_by TEXT NOT NULL, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS asset_collections(
  id TEXT PRIMARY KEY, type_id TEXT NOT NULL REFERENCES collection_types(id),
  label TEXT NOT NULL, declared_by TEXT NOT NULL, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS memberships(
  id TEXT PRIMARY KEY, collection_id TEXT NOT NULL REFERENCES asset_collections(id),
  asset_id TEXT NOT NULL, filed_by TEXT NOT NULL, standing TEXT NOT NULL,
  created_at REAL NOT NULL);
"""

DECLARE_TYPE = "declare:collection-type"
DECLARE_COLLECTION = "declare:asset-collection"
ORGANIZE = "organize:asset"

EFFECTIVE = "EFFECTIVE"
COUNTERED = "COUNTERED"

KNOWN_ROLES = frozenset({ORIGINAL, REVISION, DERIVATIVE})

SPEC_KEYS = frozenset({"required_fields", "optional_fields", "vocabularies", "admits_roles"})


class OrganizationRefused(ValueError):
    """A curatorial act was refused; `code` carries the declared refusal."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class Organization:
    """Collection types, collections, and membership for one service root."""

    def __init__(self, store: Store, authority: Authority) -> None:
        self.store = store
        self.authority = authority
        self.db = store.db
        self.now = store.now

    def _refuse(self, code: str, event: str, subject_type: str, subject_id: str,
                actor: str, detail: dict[str, Any]) -> None:
        """Receipt the refusal before raising, so a refused act is as inspectable as a commit."""
        self.store.receipt("REFUSED", event, subject_type, subject_id, actor,
                           dict(detail, reason=code))
        self.db.commit()
        raise OrganizationRefused(code, json.dumps(detail, sort_keys=True))

    # -- types ------------------------------------------------------------

    def declare_type(self, type_id: str, label: str, spec: dict[str, Any],
                     actor: str) -> str:
        """Declare the schema a collection of this type holds its members to.

        The spec names required and optional metadata fields, an optional
        controlled vocabulary per field, and which asset roles may be filed. A
        vocabulary over a field the spec never declared, or a role the service
        does not have, is refused rather than stored and quietly ignored.
        """
        event = "asset.declare-collection-type"
        self.authority.require(actor, DECLARE_TYPE, type_id, "collection-type", type_id)
        if self.type(type_id) is not None:
            self._refuse("STALE_STATE", event, "collection-type", type_id, actor,
                         {"type_id": type_id, "already_declared": True})
        normalized = self._normalize_spec(type_id, spec, actor, event)
        self.db.execute("INSERT INTO collection_types VALUES(?,?,?,?,?)",
                        (type_id, label, json.dumps(normalized, sort_keys=True), actor,
                         self.now()))
        receipt = self.store.receipt("COMMITTED", event, "collection-type", type_id, actor,
                                     {"label": label, "spec": normalized})
        self.db.commit()
        return receipt

    def _normalize_spec(self, type_id: str, spec: dict[str, Any], actor: str,
                        event: str) -> dict[str, Any]:
        """Check a declared spec against what it may say, and put it in a stable order."""
        unknown = sorted(set(spec) - SPEC_KEYS)
        if unknown:
            self._refuse("INCOMPLETE_PROPOSAL", event, "collection-type", type_id, actor,
                         {"undeclared_spec_keys": unknown})
        required = tuple(spec.get("required_fields") or ())
        optional = tuple(spec.get("optional_fields") or ())
        if not required:
            self._refuse("INCOMPLETE_PROPOSAL", event, "collection-type", type_id, actor,
                         {"required_fields": "a type requiring nothing cannot be conformed to"})
        fields = required + optional
        if len(set(fields)) != len(fields):
            repeated = sorted({name for name in fields if fields.count(name) > 1})
            self._refuse("INCOMPLETE_PROPOSAL", event, "collection-type", type_id, actor,
                         {"repeated_fields": repeated})
        vocabularies = dict(spec.get("vocabularies") or {})
        undeclared = sorted(set(vocabularies) - set(fields))
        if undeclared:
            self._refuse("POLICY_REFUSED", event, "collection-type", type_id, actor,
                         {"vocabulary_over_undeclared_field": undeclared})
        roles = tuple(spec.get("admits_roles") or sorted(KNOWN_ROLES))
        unknown_roles = sorted(set(roles) - KNOWN_ROLES)
        if unknown_roles:
            self._refuse("POLICY_REFUSED", event, "collection-type", type_id, actor,
                         {"unknown_roles": unknown_roles})
        return {"required_fields": list(required), "optional_fields": list(optional),
                "vocabularies": {key: sorted(values) for key, values in vocabularies.items()},
                "admits_roles": sorted(roles)}

    def type(self, type_id: str) -> dict[str, Any] | None:
        """One declared type with its spec parsed, or None."""
        row = self.db.execute("SELECT * FROM collection_types WHERE id=?", (type_id,)).fetchone()
        return self._type_row(row) if row else None

    def types(self) -> list[dict[str, Any]]:
        """Every declared collection type, in declaration order."""
        return [self._type_row(row) for row in
                self.db.execute("SELECT * FROM collection_types ORDER BY created_at,id")]

    @staticmethod
    def _type_row(row: sqlite3.Row) -> dict[str, Any]:
        return {"type_id": row["id"], "label": row["label"],
                "spec": json.loads(row["spec_json"]), "declared_by": row["declared_by"],
                "created_at": row["created_at"]}

    # -- collections ------------------------------------------------------

    def declare_collection(self, type_id: str, label: str, actor: str) -> dict[str, str]:
        """Open a collection of a declared type. A project is one such type."""
        event = "asset.declare-collection"
        collection = new_id("collection")
        self.authority.require(actor, DECLARE_COLLECTION, type_id,
                               "asset-collection", collection)
        if self.type(type_id) is None:
            self._refuse("TYPE_UNDECLARED", event, "asset-collection", collection, actor,
                         {"type_id": type_id})
        self.db.execute("INSERT INTO asset_collections VALUES(?,?,?,?,?)",
                        (collection, type_id, label, actor, self.now()))
        receipt = self.store.receipt("COMMITTED", event, "asset-collection", collection,
                                     actor, {"type_id": type_id, "label": label})
        self.db.commit()
        return {"collection_id": collection, "type_id": type_id, "receipt_id": receipt}

    def collection(self, collection_id: str) -> sqlite3.Row | None:
        """One collection row, or None."""
        return self.db.execute("SELECT * FROM asset_collections WHERE id=?",
                               (collection_id,)).fetchone()

    def collections(self) -> list[dict[str, Any]]:
        """Every collection with its type and its live member count."""
        rows = self.db.execute(
            "SELECT c.*, (SELECT COUNT(*) FROM memberships m WHERE m.collection_id=c.id "
            "             AND m.standing=?) AS members "
            "FROM asset_collections c ORDER BY c.created_at,c.id", (EFFECTIVE,)).fetchall()
        return [{"collection_id": row["id"], "type_id": row["type_id"], "label": row["label"],
                 "declared_by": row["declared_by"], "members": row["members"]} for row in rows]

    # -- membership -------------------------------------------------------

    def add_member(self, collection_id: str, asset_id: str, actor: str) -> dict[str, str]:
        """File an asset into a collection, if the type admits its newest role."""
        event = "asset.add-member"
        self.authority.require(actor, ORGANIZE, collection_id,
                               "collection-membership", asset_id)
        collection = self.collection(collection_id)
        if collection is None:
            self._refuse("MISSING_PRECONDITION", event, "collection-membership", asset_id,
                         actor, {"collection_id": collection_id})
        if self.db.execute("SELECT 1 FROM assets WHERE id=?", (asset_id,)).fetchone() is None:
            self._refuse("MISSING_PRECONDITION", event, "collection-membership", asset_id,
                         actor, {"asset_id": asset_id})
        if self._live_membership(collection_id, asset_id) is not None:
            self._refuse("DUPLICATE_MEMBERSHIP", event, "collection-membership", asset_id,
                         actor, {"collection_id": collection_id, "asset_id": asset_id})
        role = self.newest_role(asset_id)
        admits = self.type(collection["type_id"])["spec"]["admits_roles"]
        if role not in admits:
            self._refuse("MEMBER_KIND_REFUSED", event, "collection-membership", asset_id,
                         actor, {"role": role, "admits_roles": admits})
        membership = new_id("member")
        self.db.execute("INSERT INTO memberships VALUES(?,?,?,?,?,?)",
                        (membership, collection_id, asset_id, actor, EFFECTIVE, self.now()))
        receipt = self.store.receipt("COMMITTED", event, "collection-membership", membership,
                                     actor, {"collection_id": collection_id,
                                             "asset_id": asset_id, "role": role})
        self.db.commit()
        return {"membership_id": membership, "receipt_id": receipt, "role": role}

    def remove_member(self, membership_id: str, actor: str, reason: str) -> str:
        """Counter a membership. The filing event is never erased."""
        row = self.db.execute("SELECT * FROM memberships WHERE id=?",
                              (membership_id,)).fetchone()
        if row is None:
            raise KeyError(membership_id)
        self.authority.require(actor, "retract:record", row["collection_id"],
                               "collection-membership", membership_id)
        self.db.execute("UPDATE memberships SET standing=? WHERE id=?",
                        (COUNTERED, membership_id))
        receipt = self.store.receipt("COUNTERED", "asset.remove-member",
                                     "collection-membership", membership_id, actor,
                                     {"collection_id": row["collection_id"],
                                      "asset_id": row["asset_id"], "reason": reason})
        self.db.commit()
        return receipt

    def _live_membership(self, collection_id: str, asset_id: str) -> sqlite3.Row | None:
        return self.db.execute(
            "SELECT * FROM memberships WHERE collection_id=? AND asset_id=? AND standing=?",
            (collection_id, asset_id, EFFECTIVE)).fetchone()

    def newest_role(self, asset_id: str) -> str:
        """The role of the newest version; an asset with no version at all has none."""
        row = self.db.execute(
            "SELECT role FROM versions WHERE asset_id=? ORDER BY created_at DESC, id DESC LIMIT 1",
            (asset_id,)).fetchone()
        return row["role"] if row else "NONE"

    def members(self, collection_id: str) -> list[dict[str, Any]]:
        """Assets currently filed in a collection, oldest filing first."""
        rows = self.db.execute(
            "SELECT m.id, m.asset_id, m.filed_by, m.created_at, a.label "
            "FROM memberships m JOIN assets a ON a.id = m.asset_id "
            "WHERE m.collection_id=? AND m.standing=? ORDER BY m.created_at,m.id",
            (collection_id, EFFECTIVE)).fetchall()
        return [dict(row) for row in rows]

    def unfiled(self) -> list[str]:
        """Assets in no collection at all - the pile every library grows."""
        return [row["id"] for row in self.db.execute(
            "SELECT a.id FROM assets a WHERE NOT EXISTS ("
            "  SELECT 1 FROM memberships m WHERE m.asset_id=a.id AND m.standing=?) "
            "ORDER BY a.id", (EFFECTIVE,))]


__all__ = ["Organization", "OrganizationRefused", "SCHEMA"]
