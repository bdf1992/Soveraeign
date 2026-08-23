"""Evaluate one kernel transition request against the declared transition table.

`SPEC.md` states the transition contract in prose: every transition checks its
declared pre-state, a stale pre-state cannot settle, an executor report is not
settlement, and settlement needs an observation the executor did not produce.
Nothing compiled those sentences, so each participant restated them privately -
the ticket workflow in its own table, the Asset Service in its own SQL. This
module reads `contracts/kernel-transitions.json` and applies it, so the same
sentences hold wherever they are checked from.

It decides legality only. It records nothing, holds no state, and grants
nothing: a permitted decision means the declared preconditions hold, never that
the transition has happened or that the caller may make it happen.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class Decision:
    """The kernel's answer for one request."""

    permitted: bool
    reason_code: str | None
    detail: str

    def render(self) -> str:
        """Return a one-line human reading of the decision."""
        if self.permitted:
            return f"PERMITTED: {self.detail}"
        return f"REFUSED {self.reason_code}: {self.detail}"


def load_table(root: Path) -> dict[str, Any]:
    """Load the declared kernel transition table."""
    path = root / "contracts" / "kernel-transitions.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _entry(table: dict[str, Any], transition: str) -> dict[str, Any] | None:
    for candidate in table["transitions"]:
        if candidate["transition"] == transition:
            return candidate
    return None


def _refuse(code: str, detail: str) -> Decision:
    return Decision(False, code, detail)


def _check_preconditions(request: dict[str, Any], entry: dict[str, Any]) -> Decision | None:
    """Every precondition key the table names must be declared and non-empty."""
    declared = request.get("declared") or {}
    absent = [key for key in entry["preconditions"]
              if key not in declared or declared[key] in (None, "", [], {})]
    if absent:
        return _refuse("MISSING_PRECONDITION", f"absent or empty: {', '.join(sorted(absent))}")
    return None


def _check_pre_state(request: dict[str, Any], current: dict[str, Any]) -> Decision | None:
    """A transition that acts on state must act on the state that is actually there."""
    claimed = request.get("pre_state_digest")
    if not claimed:
        return _refuse("STALE_STATE", "the request declares no pre-state to check")
    actual = current.get("state_digest")
    if actual is not None and claimed != actual:
        return _refuse("STALE_STATE", "the declared pre-state is not the current state")
    return None


def _check_lease(request: dict[str, Any], current: dict[str, Any]) -> Decision | None:
    """A lease is a fencing token: newer fences supersede older ones outright."""
    lease = request.get("lease")
    if not lease:
        return _refuse("STALE_LEASE", "the request holds no lease")
    holder = current.get("lease_holder_id")
    if holder is not None and lease["holder_id"] != holder:
        return _refuse("STALE_LEASE", f"{lease['holder_id']} does not hold the current lease")
    fence = current.get("lease_fence")
    if fence is not None and lease["fence"] != fence:
        return _refuse(
            "STALE_LEASE",
            f"fence {lease['fence']} was superseded by fence {fence}",
        )
    now = current.get("now")
    if now is not None and lease["expires_at"] <= now:
        return _refuse("STALE_LEASE", "the lease expired before the request was made")
    return None


def _check_observation(request: dict[str, Any], current: dict[str, Any]) -> Decision | None:
    """Settlement needs an observation, and not one the executor made of itself."""
    observation = request.get("observation")
    if not observation:
        return _refuse("OBSERVATION_MISSING", "settlement was requested with no observation")
    if not observation.get("satisfactory"):
        return _refuse("OBSERVATION_MISSING", "the offered observation is not satisfactory")
    reporter = current.get("reporter_id")
    if reporter is not None and observation["observer_id"] == reporter:
        return _refuse(
            "OBSERVER_NOT_INDEPENDENT",
            f"{observation['observer_id']} produced the report it offers as observation",
        )
    return None


def _check_independent_observer(
    request: dict[str, Any], current: dict[str, Any]
) -> Decision | None:
    """An observation of one's own work is a report wearing an observation's name."""
    observer = (request.get("declared") or {}).get("observer_id")
    relation = (request.get("declared") or {}).get("observer_relation")
    reporter = current.get("reporter_id")
    if relation == "SELF":
        return _refuse("OBSERVER_NOT_INDEPENDENT", "the observer declares itself the executor")
    if reporter is not None and observer == reporter:
        return _refuse(
            "OBSERVER_NOT_INDEPENDENT",
            f"{observer} produced the report it proposes to observe",
        )
    return None


def _check_authority(request: dict[str, Any], entry: dict[str, Any]) -> Decision | None:
    """Verification authority cannot ratify a judgement claim."""
    required = entry.get("requires_authority_type")
    if not required:
        return None
    authority = request.get("authority")
    if not authority:
        return _refuse("AUTHORITY_REFUSED", f"{entry['transition']} needs a live {required} grant")
    if authority["authority_type"] != required:
        return _refuse(
            "AUTHORITY_REFUSED",
            f"{authority['authority_type']} authority cannot perform {entry['transition']}",
        )
    return None


SETTLING_OUTCOMES = ("COMMITTED", "FAILED", "UNRESOLVED", "COUNTERED")


def evaluate(
    request: dict[str, Any],
    table: dict[str, Any],
    current: dict[str, Any] | None = None,
) -> Decision:
    """Decide whether one transition request satisfies the declared kernel contract.

    ``current`` carries what the kernel can see of the world the request acts on:
    ``state_digest``, ``lease_holder_id``, ``lease_fence``, ``reporter_id``, and
    ``now``. A key the caller omits is unknown rather than satisfied, so the check
    that depends on it is skipped instead of silently passing.
    """
    current = current or {}
    transition = request.get("transition")
    entry = _entry(table, transition)
    if entry is None:
        return _refuse("UNKNOWN_TRANSITION", f"{transition!r} is not declared in this table")

    if request.get("effect_class") in table.get("phase_refused_effect_classes", []):
        return _refuse(
            "EFFECT_CLASS_REFUSED",
            f"{request['effect_class']} is refused in the current phase",
        )

    outcome = request.get("requested_outcome")
    if entry.get("settles") is False and outcome in SETTLING_OUTCOMES:
        return _refuse(
            "STALE_LEASE" if entry["transition"] == "report_run" else "MISSING_PRECONDITION",
            f"{entry['transition']} records a report and may not settle it",
        )

    for check in (
        _check_preconditions(request, entry),
        _check_authority(request, entry),
    ):
        if check is not None:
            return check

    if entry.get("requires_exact_pre_state"):
        refusal = _check_pre_state(request, current)
        if refusal is not None:
            return refusal
    if entry.get("requires_current_lease"):
        refusal = _check_lease(request, current)
        if refusal is not None:
            return refusal
    if entry.get("requires_independent_observer"):
        refusal = _check_independent_observer(request, current)
        if refusal is not None:
            return refusal
    if entry.get("requires_observation"):
        refusal = _check_observation(request, current)
        if refusal is not None:
            return refusal

    return Decision(True, None, f"{entry['transition']} may commit as {entry['commit']}")
