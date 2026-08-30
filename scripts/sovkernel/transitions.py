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
import unicodedata

#: Unicode's Other category, which no address is made of: control, format (where U+200B
#: ZERO WIDTH SPACE and U+FEFF live), surrogate, private use, unassigned. A lone
#: surrogate is not UTF-8 encodable, so admitting one crashes the receipt recording it.
#: Assigned letters and symbols that merely render blank in some fonts (U+3164, U+2800)
#: are admitted: which glyphs a font draws is not this boundary's to decide.
UNREADABLE_CATEGORIES = frozenset({"Cc", "Cf", "Cn", "Co", "Cs"})


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
    table = json.loads(path.read_text(encoding="utf-8"))
    authorization = root / "contracts" / "external-effect-authorization.json"
    table["_authorization"] = json.loads(authorization.read_text(encoding="utf-8"))
    return table


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


def _addresses_a_proof(address: Any) -> bool:
    """Whether this value is a string carrying a character a reader could follow.

    ``str.strip()`` removes whitespace and stops there, so ``"\\u200b"`` survived the
    emptiness test while rendering as nothing. The rule is one character outside both
    whitespace and Unicode's Other category, and it grades the receipt address as well
    as the evidence because the contract demands the same of both.
    """
    if not isinstance(address, str):
        return False
    return any(
        not char.isspace() and unicodedata.category(char) not in UNREADABLE_CATEGORIES
        for char in address
    )


def _discharged(scope: dict, authorization: dict) -> bool:
    """Whether the request discharges, by id, every precondition its verb carries.

    A precondition binds the verbs it names rather than the whole scope. The kernel
    cannot read the live remote the statements are about; it refuses the effect unless
    the request names each precondition and the evidence discharging it, and refuses an
    attestation naming a precondition the verb does not carry.

    Evidence must be a string with visible content: a precondition is discharged by an
    address a reader can follow, so a bare ``true`` is the caller vouching for itself and
    a number or a list addresses nothing. ``evaluate`` is reachable without the crossing
    schema having run, so the shape is refused here as well as there. Emptiness is
    decided by ``_addresses_a_proof``, because ``str.strip`` leaves a zero-width space.
    """
    verb = authorization.get("verb")
    declared = {
        precondition["id"]
        for precondition in scope.get("preconditions", [])
        if verb in precondition.get("verbs", [])
    }
    discharged = authorization.get("preconditions_discharged")
    if discharged is None:
        discharged = {}
    if not isinstance(discharged, dict):
        return False
    for name in declared:
        if not _addresses_a_proof(discharged.get(name)):
            return False
    return not set(discharged) - declared


def _authorized(table: dict, request: dict) -> bool:
    """Whether a declared scope admits this external effect, with a receipt.

    SPEC.md no longer refuses ``EXTERNAL_WORLD`` by class. The question is
    whether ``contracts/external-effect-authorization.json`` carries the scope,
    whether that scope carries the verb, whether the verb is refused by name,
    whether the attempt will leave a record, and whether every precondition the
    scope declares on that verb is discharged.
    """
    contract = table.get("_authorization") or {}
    authorization = request.get("authorization")
    if not isinstance(authorization, dict):
        return False
    verb = authorization.get("verb")
    if not isinstance(verb, str) or not verb or verb in contract.get("refused_verbs", {}):
        return False
    named = authorization.get("scope")
    scope = contract.get("scopes", {}).get(named) if isinstance(named, str) else None
    if scope is None or verb not in scope.get("verbs", []):
        return False
    if not _addresses_a_proof(authorization.get("receipt")):
        return False
    return _discharged(scope, authorization)


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

    if request.get("effect_class") == "EXTERNAL_WORLD" and not _authorized(table, request):
        return _refuse(
            "EXTERNAL_EFFECT_UNAUTHORIZED",
            "an external effect outside every declared scope, using a verb refused by name, "
            "leaving no receipt, or not discharging a precondition its verb carries "
            "(contracts/external-effect-authorization.json)",
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
