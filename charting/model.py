"""Dependency-free validation and projection for experimental typed contract graphs."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any


class ChartingError(ValueError):
    """Raised when an experimental charting declaration is invalid."""


_ALLOWED_POINT_KINDS = {
    "binding",
    "capability",
    "concern",
    "implementation",
    "operator",
    "paradigm",
    "requirement",
    "skill",
    "stance",
    "workflow",
}

_ALLOWED_CROSSING_KINDS = {
    "binds",
    "blocks",
    "implemented_by",
    "provides",
    "realizes",
    "requires",
    "uses",
}

_ALLOWED_RELATIONS = {
    ("binding", "provides", "implementation"),
    ("implementation", "realizes", "skill"),
    ("skill", "requires", "requirement"),
    ("requirement", "binds", "capability"),
}


@dataclass(frozen=True)
class Point:
    """One addressed typed point in an experimental contract graph."""

    id: str
    kind: str
    label: str
    source: str
    attributes: dict[str, Any]


@dataclass(frozen=True)
class Crossing:
    """One typed directed relation between two points."""

    id: str
    kind: str
    source: str
    target: str
    provenance: str
    constraints: dict[str, Any]


class ContractGraph:
    """Validate and project a small typed graph without granting it authority."""

    def __init__(self, declaration: dict[str, Any]) -> None:
        self.declaration = declaration
        self.points = self._load_points(declaration.get("points", []))
        self.crossings = self._load_crossings(declaration.get("crossings", []))
        self.paradigms = self._load_paradigms(declaration.get("paradigms", []))
        self.omissions = self._load_omissions(declaration.get("omissions", []))
        self._validate_crossings()

    @classmethod
    def from_dict(cls, declaration: dict[str, Any]) -> "ContractGraph":
        return cls(declaration)

    def _load_points(self, values: list[dict[str, Any]]) -> dict[str, Point]:
        points: dict[str, Point] = {}
        for raw in values:
            point_id = _required_text(raw, "id")
            kind = _required_text(raw, "kind")
            if kind not in _ALLOWED_POINT_KINDS:
                raise ChartingError(f"unsupported point kind: {kind}")
            if point_id in points:
                raise ChartingError(f"duplicate point id: {point_id}")
            points[point_id] = Point(
                id=point_id,
                kind=kind,
                label=_required_text(raw, "label"),
                source=_required_text(raw, "source"),
                attributes=dict(raw.get("attributes", {})),
            )
        return points

    def _load_crossings(self, values: list[dict[str, Any]]) -> dict[str, Crossing]:
        crossings: dict[str, Crossing] = {}
        for raw in values:
            crossing_id = _required_text(raw, "id")
            kind = _required_text(raw, "kind")
            if kind not in _ALLOWED_CROSSING_KINDS:
                raise ChartingError(f"unsupported crossing kind: {kind}")
            if crossing_id in crossings:
                raise ChartingError(f"duplicate crossing id: {crossing_id}")
            crossings[crossing_id] = Crossing(
                id=crossing_id,
                kind=kind,
                source=_required_text(raw, "source"),
                target=_required_text(raw, "target"),
                provenance=_required_text(raw, "provenance"),
                constraints=dict(raw.get("constraints", {})),
            )
        return crossings

    def _load_paradigms(self, values: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        paradigms: dict[str, dict[str, Any]] = {}
        for raw in values:
            paradigm_id = _required_text(raw, "id")
            if paradigm_id in paradigms:
                raise ChartingError(f"duplicate paradigm id: {paradigm_id}")
            traverse = raw.get("traverse", [])
            if not traverse or any(kind not in _ALLOWED_CROSSING_KINDS for kind in traverse):
                raise ChartingError(f"paradigm {paradigm_id} has invalid traversal kinds")
            paradigms[paradigm_id] = dict(raw)
        return paradigms

    @staticmethod
    def _load_omissions(values: Any) -> list[str]:
        if not isinstance(values, list):
            raise ChartingError("graph omissions must be a list")
        omissions: list[str] = []
        for value in values:
            if not isinstance(value, str) or not value.strip():
                raise ChartingError("graph omission must be non-empty text")
            omissions.append(value.strip())
        return omissions

    def _validate_crossings(self) -> None:
        for crossing in self.crossings.values():
            if crossing.source not in self.points:
                raise ChartingError(f"crossing {crossing.id} has unknown source")
            if crossing.target not in self.points:
                raise ChartingError(f"crossing {crossing.id} has unknown target")
            source_kind = self.points[crossing.source].kind
            target_kind = self.points[crossing.target].kind
            relation = (source_kind, crossing.kind, target_kind)
            if relation not in _ALLOWED_RELATIONS:
                raise ChartingError(f"unsupported semantic relation: {relation}")

    def chart(self, root: str, paradigm_id: str, *, max_depth: int = 4) -> dict[str, Any]:
        """Project one bounded local chart from a root using typed traversal rules."""

        if root not in self.points:
            raise ChartingError(f"unknown chart root: {root}")
        if paradigm_id not in self.paradigms:
            raise ChartingError(f"unknown paradigm: {paradigm_id}")
        if max_depth < 0:
            raise ChartingError("max_depth must be non-negative")

        paradigm = self.paradigms[paradigm_id]
        traversable = set(paradigm["traverse"])
        included_points = {root}
        included_crossings: list[Crossing] = []
        queue: deque[tuple[str, int]] = deque([(root, 0)])

        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for crossing in self.crossings.values():
                if crossing.source != current or crossing.kind not in traversable:
                    continue
                included_crossings.append(crossing)
                if crossing.target not in included_points:
                    included_points.add(crossing.target)
                    queue.append((crossing.target, depth + 1))

        omissions = list(dict.fromkeys([*self.omissions, *paradigm.get("omissions", [])]))
        return {
            "chart_version": "0.1-experimental",
            "paradigm": paradigm_id,
            "root": root,
            "source_contract": self.declaration.get("contract_id"),
            "source_revision": self.declaration.get("source_revision"),
            "points": [self._point_dict(self.points[point_id]) for point_id in sorted(included_points)],
            "crossings": [self._crossing_dict(value) for value in included_crossings],
            "omissions": omissions,
            "governance": {
                "projection_only": True,
                "grants_authority": False,
                "requires_live_gate_recheck": True,
            },
        }

    @staticmethod
    def _point_dict(point: Point) -> dict[str, Any]:
        return {
            "id": point.id,
            "kind": point.kind,
            "label": point.label,
            "source": point.source,
            "attributes": point.attributes,
        }

    @staticmethod
    def _crossing_dict(crossing: Crossing) -> dict[str, Any]:
        return {
            "id": crossing.id,
            "kind": crossing.kind,
            "source": crossing.source,
            "target": crossing.target,
            "provenance": crossing.provenance,
            "constraints": crossing.constraints,
        }


def _required_text(value: dict[str, Any], field: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result.strip():
        raise ChartingError(f"{field} must be non-empty text")
    return result
