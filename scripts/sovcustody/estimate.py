"""Grade a cost claim against the dimension registry, and read its variance.

`contracts/estimation.json` declares the dimensions; this module refuses the
four things the JSON Schema cannot see. The one worth stating plainly: a
dimension declaring itself gradeable while naming nowhere to read the measured
actual is refused, because it would otherwise sit on a board looking like a
measurement for as long as anybody cared to look.

Variance is reported, never settled. The participant that estimated may record
what it measured; deciding what the gap means is an observation, and an
observation from inside the build is not one.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, NamedTuple
import json

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "contracts" / "estimation.json"


class Defect(NamedTuple):
    """One refusal, named by its code and the exact thing that produced it."""

    code: str
    detail: str


def _registry() -> dict[str, Any]:
    return json.loads(REGISTRY.read_bytes().decode("utf-8"))


def dimensions() -> dict[str, dict[str, Any]]:
    """Declared dimensions keyed by id."""
    return {str(row["id"]): row for row in _registry()["dimensions"]}


def required_at(stage: str, ordinal_of) -> set[str]:
    """Dimension ids a ticket at `stage` must carry.

    A dimension is required from the stage it names onward, so a ticket that has
    advanced owes every dimension at or below where it stands. Nothing is
    required of a ROOT_POINT beyond what the registry pins there, because sizing
    work that has not been drawn is invention.
    """
    here = ordinal_of(stage)
    if not here:
        return set()
    return {
        name
        for name, row in dimensions().items()
        if 0 < ordinal_of(str(row.get("required_from_stage") or "")) <= here
    }


def admitted_maturity(stage: str) -> str | None:
    """The firmest estimate the circuit position honestly supports."""
    for row in _registry().get("estimate_maturity", {}).get("by_stage", []):
        if row.get("stage") == stage:
            return str(row.get("admits"))
    return None


def grade_registry(declared: dict[str, dict[str, Any]] | None = None) -> list[Defect]:
    """Refuse a registry that declares a dimension nobody could ever grade.

    `declared` overrides the shipped registry so a fixture can defeat the rule
    without the repository having to carry a broken dimension to prove it.
    """
    defects: list[Defect] = []
    for name, row in (dimensions() if declared is None else declared).items():
        if row.get("derived_from"):
            defects.append(Defect(
                "SYNTHETIC_SCORE",
                f"{name} declares derived_from {row['derived_from']}; combining unlike units "
                "destroys the reading the split was for - which dimension the work ran out of",
            ))
        if row.get("graded") and not row.get("actual_source"):
            defects.append(Defect(
                "UNGRADEABLE_DIMENSION",
                f"{name} declares graded true and names no actual_source",
            ))
        if not row.get("graded") and not row.get("ungraded_because"):
            defects.append(Defect(
                "UNGRADEABLE_DIMENSION",
                f"{name} declares graded false and does not say why, so a reader "
                "cannot tell whether that is honest or an omission",
            ))
    return defects


#: Maturity, weakest first. A stage admits its own level and everything below it.
MATURITY_ORDER = ("DISCOVERY_ENVELOPE", "WIDE_RANGE", "COMMITTED_RANGE")


def grade(estimate: dict[str, Any] | None, required: set[str] | None = None,
          stage: str | None = None) -> list[Defect]:
    """Grade one estimate. An empty list admits it; anything else refuses by name."""
    if estimate is None:
        return [] if not required else [
            Defect("MISSING_REQUIRED_DIMENSION", f"no estimate at all, and {name} is required")
            for name in sorted(required)
        ]

    declared = dimensions()
    defects: list[Defect] = []
    supplied: set[str] = set()

    claimed = estimate.get("maturity")
    ceiling = admitted_maturity(stage) if stage else None
    if claimed and ceiling and MATURITY_ORDER.index(claimed) > MATURITY_ORDER.index(ceiling):
        defects.append(Defect(
            "OVERCOMMITTED_ESTIMATE",
            f"{claimed} claimed at {stage}, which admits at most {ceiling}; a delivery "
            "promise made before the work is drawn is invention",
        ))

    for row in estimate.get("dimensions") or []:
        name = str(row.get("dimension_id"))
        supplied.add(name)
        if name not in declared:
            defects.append(Defect(
                "UNKNOWN_DIMENSION",
                f"{name} is not declared in contracts/estimation.json; a consumer reports "
                "it rather than dropping it, so a dimension cannot appear on one side only",
            ))
            continue
        low, high = row.get("low"), row.get("high")
        if low is None or high is None:
            defects.append(Defect("POINT_ESTIMATE", f"{name} gives no low and high pair"))
        elif low > high:
            defects.append(Defect("INVERTED_RANGE", f"{name} low {low} exceeds high {high}"))
        if row.get("actual") is not None and not declared[name].get("graded"):
            defects.append(Defect(
                "UNGRADEABLE_DIMENSION",
                f"{name} carries an actual and the registry declares it ungraded; "
                f"{declared[name].get('ungraded_because', 'nothing measures it')}",
            ))
        observer = row.get("actual_observed_by")
        if observer and observer == estimate.get("estimated_by"):
            defects.append(Defect(
                "SELF_SETTLED_VARIANCE",
                f"{name} actual was observed by {observer}, which produced the estimate",
            ))

    for missing in sorted((required or set()) - supplied):
        defects.append(Defect(
            "MISSING_REQUIRED_DIMENSION",
            f"no estimate on {missing}, required at this stage",
        ))
    return defects


def variance(estimate: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Estimated range against measured actual, for every dimension carrying one.

    `verdict` is UNDER, WITHIN or OVER against the declared range, and PENDING
    while no actual exists. It is a reading, not a judgement: nothing here says
    an overrun was anybody's fault.
    """
    if not estimate:
        return []
    rows: list[dict[str, Any]] = []
    for row in estimate.get("dimensions") or []:
        actual = row.get("actual")
        low, high = row.get("low"), row.get("high")
        if actual is None:
            verdict = "PENDING"
        elif actual < low:
            verdict = "UNDER"
        elif actual > high:
            verdict = "OVER"
        else:
            verdict = "WITHIN"
        rows.append({
            "dimension_id": row.get("dimension_id"),
            "low": low,
            "high": high,
            "actual": actual,
            "verdict": verdict,
        })
    return rows


def declared_refusals() -> dict[str, str]:
    """Every refusal code the registry declares, with its meaning."""
    return dict(_registry()["refusals"])
