"""Conformance of a filed asset against the schema its collection type declares.

This module reads and judges; it writes no authoritative record. A finding says
what the library looks like right now, so it is derived on every call and never
stored - a stored verdict would go stale the moment someone ratified a
description, and would then be a projection nobody rebuilt.

The verdicts distinguish three states an operator otherwise conflates:

- ``CONFORMING`` - a ratified description carries the required field with a
  permitted value.
- ``CLAIMED_UNRATIFIED`` - somebody recorded the field and nobody ratified it.
  The metadata exists as a claim. `AGENTS.md` (Evidence and standing) forbids
  counting that as a fact, and a report that silently did would be the defect
  this service exists to make impossible.
- ``MISSING_FIELD`` - nothing in the record carries it at all.

``VOCABULARY_REFUSED`` and ``MEMBER_KIND_REFUSED`` are the two ways a member can
carry a value the type does not admit; the second is refused at filing time by
`organization.py` and appears here only for a type re-read after members were
filed under an earlier spec.
"""

from __future__ import annotations

from typing import Any
import json

from soveraeign_asset_service.organization import Organization
from soveraeign_asset_service.store import Store


CONFORMING = "CONFORMING"
CLAIMED_UNRATIFIED = "CLAIMED_UNRATIFIED"
MISSING_FIELD = "MISSING_FIELD"
VOCABULARY_REFUSED = "VOCABULARY_REFUSED"
MEMBER_KIND_REFUSED = "MEMBER_KIND_REFUSED"
EMPTY_COLLECTION = "EMPTY_COLLECTION"
UNFILED = "UNFILED"

#: Verdicts a conforming library carries none of.
DEFECTS = (MISSING_FIELD, VOCABULARY_REFUSED, MEMBER_KIND_REFUSED, EMPTY_COLLECTION, UNFILED)

RELATIONSHIP = "relationship"


class Librarian:
    """The organizational-schema conformance read over one service root."""

    def __init__(self, store: Store, organization: Organization) -> None:
        self.store = store
        self.organization = organization
        self.db = store.db

    def describe(self, asset_id: str) -> dict[str, dict[str, Any]]:
        """Field values an asset carries, split by whether anyone ratified them.

        Newest proposal wins within each standing, so a later description
        supersedes an earlier one without erasing it from the record.
        """
        ratified: dict[str, Any] = {}
        claimed: dict[str, Any] = {}
        rows = self.db.execute(
            "SELECT standing, payload_json FROM proposals WHERE asset_id=? "
            "ORDER BY created_at, id", (asset_id,)).fetchall()
        for row in rows:
            target = ratified if row["standing"] == "RATIFIED" else claimed
            for field, value in json.loads(row["payload_json"]).items():
                if field != RELATIONSHIP:
                    target[field] = value
        return {"ratified": ratified, "claimed": claimed}

    def _field_finding(self, field: str, required: bool, spec: dict[str, Any],
                       described: dict[str, dict[str, Any]]) -> tuple[str, Any] | None:
        """One verdict for one field, or None when an absent optional field is fine."""
        vocabulary = spec["vocabularies"].get(field)
        for standing, verdict in (("ratified", CONFORMING), ("claimed", CLAIMED_UNRATIFIED)):
            if field not in described[standing]:
                continue
            value = described[standing][field]
            if vocabulary is not None and value not in vocabulary:
                return VOCABULARY_REFUSED, value
            return verdict, value
        return (MISSING_FIELD, None) if required else None

    def conformance(self, collection_id: str) -> dict[str, Any]:
        """Every member of one collection judged against its type."""
        collection = self.organization.collection(collection_id)
        if collection is None:
            raise KeyError(collection_id)
        declared = self.organization.type(collection["type_id"])
        spec = declared["spec"]
        findings: list[dict[str, Any]] = []
        members = self.organization.members(collection_id)
        for member in members:
            asset_id = member["asset_id"]
            described = self.describe(asset_id)
            role = self.organization.newest_role(asset_id)
            if role not in spec["admits_roles"]:
                findings.append({"asset_id": asset_id, "field": None,
                                 "verdict": MEMBER_KIND_REFUSED, "value": role})
            for field in spec["required_fields"]:
                verdict = self._field_finding(field, True, spec, described)
                findings.append({"asset_id": asset_id, "field": field,
                                 "verdict": verdict[0], "value": verdict[1]})
            for field in spec["optional_fields"]:
                verdict = self._field_finding(field, False, spec, described)
                if verdict is not None:
                    findings.append({"asset_id": asset_id, "field": field,
                                     "verdict": verdict[0], "value": verdict[1]})
        if not members:
            findings.append({"asset_id": None, "field": None,
                             "verdict": EMPTY_COLLECTION, "value": None})
        return {"collection_id": collection_id, "label": collection["label"],
                "type_id": collection["type_id"], "members": len(members),
                "findings": findings, "counts": _counts(findings)}

    def report(self) -> dict[str, Any]:
        """The whole library: every collection judged, plus the assets nobody filed."""
        collections = [self.conformance(entry["collection_id"])
                       for entry in self.organization.collections()]
        unfiled = self.organization.unfiled()
        findings = [finding for entry in collections for finding in entry["findings"]]
        findings.extend({"asset_id": asset_id, "field": None, "verdict": UNFILED,
                         "value": None} for asset_id in unfiled)
        return {"types": self.organization.types(), "collections": collections,
                "unfiled": unfiled, "counts": _counts(findings),
                "defects": sum(_counts(findings).get(code, 0) for code in DEFECTS)}


def _counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    """Findings per verdict, in verdict order, with no zero rows invented."""
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding["verdict"]] = counts.get(finding["verdict"], 0) + 1
    return dict(sorted(counts.items()))


def _schema_lines(types: list[dict[str, Any]]) -> list[str]:
    """The declared schema itself, so a reader can check a verdict against its rule."""
    if not types:
        return ["", "## Declared types", "", "None. Nothing can be filed until one is declared."]
    lines = ["", "## Declared types", "",
             "| type | required | optional | vocabularies | admits |", "| --- | --- | --- | --- | --- |"]
    for declared in types:
        spec = declared["spec"]
        vocabulary = "; ".join(f"{field}: {'/'.join(values)}"
                               for field, values in spec["vocabularies"].items()) or "-"
        lines.append(f"| {declared['type_id']} | {', '.join(spec['required_fields']) or '-'} "
                     f"| {', '.join(spec['optional_fields']) or '-'} | {vocabulary} "
                     f"| {', '.join(spec['admits_roles'])} |")
    return lines


def render(report: dict[str, Any]) -> str:
    """The library report as markdown, for a human reading it in a terminal."""
    lines = ["# Asset library conformance", ""]
    lines.append(f"{len(report['collections'])} collection(s), "
                 f"{report['defects']} defect(s), "
                 f"{len(report['unfiled'])} unfiled asset(s).")
    lines.append("")
    lines.append("| verdict | count |")
    lines.append("| --- | --- |")
    for verdict, count in report["counts"].items():
        lines.append(f"| {verdict} | {count} |")
    lines.extend(_schema_lines(report.get("types") or []))
    for entry in report["collections"]:
        lines.extend(["", f"## {entry['label']} ({entry['type_id']})", "",
                      f"{entry['members']} member(s), collection `{entry['collection_id']}`.", ""])
        defects = [f for f in entry["findings"] if f["verdict"] in DEFECTS]
        if not defects:
            lines.append("No defects.")
            continue
        lines.extend(["| asset | field | verdict | value |", "| --- | --- | --- | --- |"])
        for finding in defects:
            lines.append(f"| {finding['asset_id'] or '-'} | {finding['field'] or '-'} "
                         f"| {finding['verdict']} | {finding['value'] if finding['value'] else '-'} |")
    if report["unfiled"]:
        lines.extend(["", "## Unfiled", "",
                      "In no collection at all:", ""])
        lines.extend(f"- `{asset_id}`" for asset_id in report["unfiled"])
    return "\n".join(lines) + "\n"


__all__ = ["Librarian", "render", "DEFECTS"]
