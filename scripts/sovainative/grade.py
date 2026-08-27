"""Derive one surface's AI-native reading from what the record actually evidences.

The verdict is derived, never selected. `AI-NATIVE.md` says so directly, and the record
shape carries no verdict field, so a record that states its own result fails the shape
rather than being argued with. Everything here grades what a record claims against what it
shows: a score above NONE with no observable evidence, a qualification resting on a seed
scenario that executes nothing, a substantive-operation judgement made by something that
is not a registered human principal.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovainative.standard import SCORE_ORDER  # noqa: E402
from sovkernel import jsonschema  # noqa: E402
from sovsession import principals  # noqa: E402

INVALID, OPEN, COMPLETE = "INVALID", "OPEN", "COMPLETE"
DECORATION, TRUTH_CAPABLE = "DECORATION", "TRUTH_CAPABLE"
AI_NATIVE, QUALIFIED = "AI_NATIVE", "SOVERAEIGN_QUALIFIED"


def _defect(code: str, detail: str) -> dict:
    return {"code": code, "detail": detail}


def shape_defects(record: object, schema: dict) -> list[dict]:
    """Grade the record against its declared shape, including the absent verdict field."""
    if isinstance(record, dict) and "verdict" in record:
        stated = record["verdict"]
        return [_defect("VERDICT_DECLARED",
                        f"the record states verdict {stated!r}; the verdict is derived from "
                        "the recorded scores and is never selected directly")]
    return [_defect("SHAPE_REFUSED", d) for d in jsonschema.validate(record, schema, schema)]


def _evidence_defects(name: str, kind: str, entry: dict, table: dict,
                      statuses: dict[str, str], claimed: bool) -> list[dict]:
    """Grade one axis or qualification's evidence against what it claims."""
    defects: list[dict] = []
    evidence = entry.get("evidence") or []
    asserted = entry.get("score") or entry.get("result")
    if claimed and not evidence:
        defects.append(_defect("EVIDENCE_ABSENT",
                               f"{kind} {name} claims {asserted} and identifies no "
                               "observable evidence"))
    executable = set(table["executable_scenario_status"])
    for item in evidence:
        if item.get("kind") != "scenario":
            continue
        cited = item.get("reference", "")
        if cited not in statuses:
            defects.append(_defect(
                "SCENARIO_UNKNOWN",
                f"{kind} {name} cites {cited}, which is not a founding scenario"))
        elif claimed and statuses[cited] not in executable:
            defects.append(_defect(
                "SCENARIO_NOT_EXECUTABLE",
                f"{kind} {name} rests on {cited}, which is at {statuses[cited]} standing "
                "and executes nothing"))
    return defects


def reviewer_defects(record: dict, table: dict, registry: dict | None) -> list[dict]:
    """Grade who made the substantive-operation judgement, which no model may make."""
    earn_it = record.get("earn_it") or {}
    if earn_it.get("judgement") == "OPEN":
        return []
    reviewer = earn_it.get("reviewer")
    if registry is None:
        return [_defect("REVIEWER_UNREGISTERED",
                        f"reviewer {reviewer!r} cannot be resolved: no principal registry")]
    seated = principals.index(registry).get(reviewer)
    if seated is None:
        return [_defect("REVIEWER_UNREGISTERED",
                        f"reviewer {reviewer!r} is not a registered principal")]
    if seated.get("kind") != table["earn_it"]["reviewer_must_be"]:
        return [_defect("REVIEWER_NOT_HUMAN",
                        f"reviewer {reviewer!r} is a {seated.get('kind')} principal; the "
                        "substantive-operation check is a human judgement")]
    return []


def gate_defects(record: dict) -> list[dict]:
    """Refuse a target-bar claim on a surface the gate says cannot be reached.

    AI-NATIVE.md makes reachability the gate: an unreachable surface cannot be AI-native
    regardless of every other score. The nine qualifications are layered above that
    minimum, so a record scoring reachability NONE while passing one of them is claiming
    something above a bar it does not reach.
    """
    if record["axes"]["reachability"]["score"] != "NONE":
        return []
    passed = sorted(q for q, e in record["qualifications"].items() if e["result"] == "PASS")
    if not passed:
        return []
    return [_defect("CONTRADICTORY_SCORE",
                    "reachability is NONE, which the standard makes the gate, while "
                    + ", ".join(passed) + " is claimed PASS above it")]


def content_defects(record: dict, table: dict, statuses: dict[str, str],
                    registry: dict | None) -> list[dict]:
    """Grade evidence, cited scenarios, the gate and the reviewer of a shape-valid record."""
    defects: list[dict] = []
    missing = sorted(set(table["qualifications"]) - set(record["qualifications"]))
    if missing:
        defects.append(_defect("QUALIFICATION_MISSING",
                               "the record does not answer " + ", ".join(missing)))
    for name, entry in record["axes"].items():
        defects += _evidence_defects(name, "axis", entry, table, statuses,
                                     entry.get("score") != "NONE")
    for name, entry in record["qualifications"].items():
        defects += _evidence_defects(name, "qualification", entry, table, statuses,
                                     entry.get("result") == "PASS")
    return defects + gate_defects(record) + reviewer_defects(record, table, registry)


def _at_least(record: dict, axis: str, score: str) -> bool:
    return SCORE_ORDER.index(record["axes"][axis]["score"]) >= SCORE_ORDER.index(score)


def derive_verdict(record: dict, table: dict) -> tuple[str, list[str]]:
    """Derive the verdict from the recorded scores, and say what held it where it landed.

    The fourth branch of the derived-verdict list in AI-NATIVE.md - reachable and
    substantive but below the supporting threshold, TRUTH_CAPABLE when a structural axis
    is present - has no live case under the reading that "present" means scored above
    NONE, because that is the same condition as the threshold it is said to be below. It
    is implemented literally and the branch is dead; decisions/0070 carries the residual.
    """
    structural = [a for a in table["structural_axes"] if _at_least(record, a, "PARTIAL")]
    if not _at_least(record, "reachability", "PARTIAL"):
        return ((TRUTH_CAPABLE, ["unreachable, with a structural axis present"]) if structural
                else (DECORATION, ["unreachable, with no structural axis present"]))
    if record["earn_it"]["judgement"] != "SUBSTANTIVE":
        return DECORATION, ["reachable, but the operation is judged bolted on"]
    if not structural:
        return DECORATION, ["reachable and substantive, with no structural axis above NONE"]
    short = [a for a in table["soveraeign_bar"]["axes_at_full"]
             if record["axes"][a]["score"] != "FULL"]
    failing = [q for q, e in record["qualifications"].items() if e["result"] != "PASS"]
    if short or failing:
        return AI_NATIVE, ([f"{a} is not FULL" for a in short]
                           + [f"{q} is not PASS" for q in failing])
    return QUALIFIED, []


def grade(record: object, table: dict, schema: dict, statuses: dict[str, str],
          registry: dict | None) -> dict:
    """The whole reading: defects first, then state, then a verdict only if one is earned."""
    defects = shape_defects(record, schema)
    if defects:
        return {"state": INVALID, "verdict": None, "defects": defects, "held_by": []}
    assert isinstance(record, dict)
    defects = content_defects(record, table, statuses, registry)
    if defects:
        return {"state": INVALID, "verdict": None, "defects": defects, "held_by": []}
    if record["earn_it"]["judgement"] == "OPEN":
        return {"state": OPEN, "verdict": None, "defects": [],
                "held_by": ["the substantive-operation judgement has not landed"]}
    verdict, held = derive_verdict(record, table)
    return {"state": COMPLETE, "verdict": verdict, "defects": [], "held_by": held}
