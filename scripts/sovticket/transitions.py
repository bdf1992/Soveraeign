"""Evaluate a proposed ticket standing change against the declared transition table.

The evaluator answers one question: may this coordination surface accept this standing
change from this actor on this evidence. An ``ALLOWED`` answer is not a settlement, a
witness, or a ratification. Standing changes land in the owning governing documents;
this module only refuses the ones the contract already forbids.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import unicodedata

OPEN_FINDING_STATUSES = frozenset({"PROPOSED", "REPRODUCED"})
DEFAULT_REQUIRED_DRY_ROUNDS = 2
#: Unicode's Other category, which no address is made of: control, format (where U+200B
#: ZERO WIDTH SPACE and U+FEFF live), surrogate, private use, unassigned. A lone
#: surrogate is not UTF-8 encodable, so admitting one crashes the receipt recording it.
#: Assigned letters and symbols that merely render blank in some fonts (U+3164 HANGUL
#: FILLER, U+2800 BRAILLE PATTERN BLANK) are admitted: which glyphs a font draws is not
#: this boundary's to decide, and the rule has to be one a reader can state.
UNREADABLE_CATEGORIES = frozenset({"Cc", "Cf", "Cn", "Co", "Cs"})


@dataclass(frozen=True)
class Decision:
    """The outcome of evaluating one transition request."""

    allowed: bool
    reason_code: str | None
    detail: str

    def render(self) -> str:
        """Return a single human-readable line for a log, comment, or report."""
        if self.allowed:
            return f"ALLOWED: {self.detail}"
        return f"REFUSED [{self.reason_code}]: {self.detail}"


def load_authorization(root: Path) -> dict[str, Any]:
    """Load the declared external-effect authorization."""
    path = root / "contracts" / "external-effect-authorization.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _addresses_a_proof(address: Any) -> bool:
    """Whether this value is a string carrying a character a reader could follow.

    ``str.strip()`` removes whitespace and stops there, so ``"\\u200b"`` survived the
    emptiness test while rendering as nothing at all. The rule is one character outside
    Unicode's Other category and outside whitespace; it grades both the evidence
    discharging a precondition and the receipt address the attempt promises to leave,
    because the contract makes the same demand of both. The kernel decides this the same
    way in its own module, so ``contracts/kernel-parity.json`` compares two.
    """
    if not isinstance(address, str):
        return False
    return any(
        not char.isspace() and unicodedata.category(char) not in UNREADABLE_CATEGORIES
        for char in address
    )


def _check_scope_preconditions(
    scope: dict[str, Any], authorization: dict[str, Any]
) -> Decision | None:
    """Refuse an admitted verb whose declared preconditions this request does not discharge.

    A precondition binds the verbs it names rather than the whole scope, so a label write
    is never asked for the body proofs. Every precondition the verb does carry is decided
    by reading the live remote, which this evaluator cannot do. What it can do, and what
    nothing did before, is refuse the effect unless the request names each precondition and
    the evidence that discharged it. An attestation naming a precondition the verb does not
    carry discharges nothing and is refused too, so a caller cannot pad its way past a
    precondition the contract later adds.

    Evidence has to be a string with something visible in it, because a precondition is
    discharged by an address a reader can follow. A bare ``true`` is the caller
    vouching for itself, which the contract's precondition_model says is not a
    boundary; a number or a list addresses nothing either. The schema refuses all of
    them by shape, and this refuses them again, because ``evaluate`` is reachable from
    callers that never validated the request. Emptiness is decided by
    ``_addresses_a_proof`` rather than ``str.strip``, which leaves a zero-width space
    standing.
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
        return Decision(
            False, "EXTERNAL_EFFECT_PRECONDITION_UNMET",
            f"{verb!r} carries a discharge block this boundary cannot read: "
            f"{type(discharged).__name__} is not a mapping of precondition id to evidence")
    missing = sorted(name for name in declared if not _addresses_a_proof(discharged.get(name)))
    if missing:
        return Decision(
            False, "EXTERNAL_EFFECT_PRECONDITION_UNMET",
            f"{verb!r} carries preconditions this request does not discharge: "
            f"{', '.join(missing)}")
    # Rendered through ``str`` because a discharge block reaching here need not have come
    # through the schema: a key that is not a string sorts against no declared id and
    # raised TypeError, which is crashing rather than refusing. The kernel's set
    # difference never sorted, so this side raised where that one refused.
    undeclared = sorted(str(name) for name in set(discharged) - declared)
    if undeclared:
        return Decision(
            False, "EXTERNAL_EFFECT_PRECONDITION_UNMET",
            f"{verb!r} carries no precondition named {', '.join(undeclared)}")
    return None


def _check_external_effect(table: dict[str, Any], request: dict[str, Any]) -> Decision | None:
    """Refuse an external effect that no declared scope admits.

    Phase I once refused ``EXTERNAL_WORLD`` by class, which kept irreversible acts
    behind an owner and ordinary coordination behind one too. The authorization
    contract separates them: an effect inside a declared scope, carrying a receipt,
    proceeds; every refused verb stays refused whatever scope is claimed; and a verb
    the scope guards with preconditions proceeds only once the request discharges them.
    """
    authorization = request.get("authorization")
    contract = table.get("_authorization")
    if contract is None:
        return Decision(
            False, "EXTERNAL_EFFECT_UNAUTHORIZED",
            "no external-effect authorization is loaded for this table")
    # A truthy non-mapping raised AttributeError out of the `.get` below rather than
    # refusing, so the block's shape is checked before anything is read out of it.
    if not isinstance(authorization, dict) or not authorization:
        return Decision(
            False, "EXTERNAL_EFFECT_UNAUTHORIZED",
            "EXTERNAL_WORLD declared with no authorized scope this boundary can read")
    verb = authorization.get("verb")
    # The kernel refuses a falsy verb before anything else, and leaving that to the scope
    # check held only while every declared `verbs` list was well formed: a contract
    # carrying "" among a scope's verbs admitted an empty verb here and not there, the
    # divergence kernel-parity.json exists to catch. Every field this boundary looks a
    # contract key up by is also pinned to `str` first, here and for `scope` below, since
    # both lookups raised TypeError on an unhashable value instead of refusing. The
    # rendering is bounded because the value is the caller's, not this module's.
    if not isinstance(verb, str) or not verb:
        return Decision(
            False, "EXTERNAL_EFFECT_OUT_OF_SCOPE",
            f"the request names no verb this boundary can read: {verb!r:.60}")
    if verb in contract.get("refused_verbs", {}):
        return Decision(
            False, "EXTERNAL_EFFECT_VERB_REFUSED",
            f"{verb!r}: {contract['refused_verbs'][verb]}")
    named = authorization.get("scope")
    scope = contract.get("scopes", {}).get(named) if isinstance(named, str) else None
    if scope is None:
        return Decision(
            False, "EXTERNAL_EFFECT_OUT_OF_SCOPE", f"{named!r:.60} is not a declared scope")
    if verb not in scope.get("verbs", []):
        return Decision(
            False, "EXTERNAL_EFFECT_OUT_OF_SCOPE",
            f"{scope['target']} does not admit {verb!r}")
    # Graded the same way evidence is: the contract says an effect with no receipt is
    # indistinguishable from one that never happened, and a receipt address a reader
    # cannot see is no receipt. Truthiness alone admitted `7`, `True` and a zero-width
    # space here while the discharge check one call below refused all three.
    if not _addresses_a_proof(authorization.get("receipt")):
        return Decision(
            False, "EXTERNAL_EFFECT_WITHOUT_RECEIPT",
            "an external effect that leaves no receipt is indistinguishable from one that "
            "never happened")
    return _check_scope_preconditions(scope, authorization)


def load_table(root: Path) -> dict[str, Any]:
    """Load the declared transition table from the repository contracts directory."""
    path = root / "contracts" / "ticket-transitions.json"
    table = json.loads(path.read_text(encoding="utf-8"))
    table["_authorization"] = load_authorization(root)
    return table


def _find(table: dict[str, Any], source: str, target: str) -> dict[str, Any] | None:
    """Return the declared transition for a from/to pair, or None."""
    for entry in table["transitions"]:
        if entry["from"] == source and entry["to"] == target:
            return entry
    return None


def _skipped(table: dict[str, Any], source: str, target: str) -> bool:
    """Report whether the pair skips a declared intermediate standing."""
    order = table["order"]
    if source not in order or target not in order:
        return False
    return order.index(target) - order.index(source) > 1


def _missing_evidence(entry: dict[str, Any], request: dict[str, Any]) -> list[str]:
    """Return the required evidence keys that are absent or empty."""
    evidence = request.get("evidence") or {}
    return [key for key in entry.get("requires_evidence", []) if not evidence.get(key)]


def _check_purple(request: dict[str, Any]) -> Decision | None:
    """Return a refusal when the verification dyad has not settled, else None."""
    receipt = request.get("purple_receipt")
    if not receipt:
        return Decision(False, "PURPLE_NOT_SETTLED", "no engagement receipt accompanies the request")
    required = receipt.get("required_dry_rounds", DEFAULT_REQUIRED_DRY_ROUNDS)
    if receipt.get("dry_rounds", 0) < required:
        return Decision(
            False,
            "PURPLE_NOT_SETTLED",
            f"{receipt.get('dry_rounds', 0)} dry rounds is below the declared exit criterion {required}",
        )
    red_actor = receipt.get("red_operator_actor_id")
    for finding in receipt.get("findings", []):
        finding_id = finding.get("finding_id", "<unnamed>")
        status = finding.get("status")
        if status in OPEN_FINDING_STATUSES:
            return Decision(False, "FINDING_UNRESOLVED", f"{finding_id} is still {status}")
        if status != "CONFIRMED":
            continue
        if not finding.get("fixture_pointer"):
            return Decision(
                False,
                "FINDING_WITHOUT_FIXTURE",
                f"{finding_id} is confirmed with no permanent defeating fixture",
            )
        reproducer = finding.get("reproduced_by_actor_id")
        if not reproducer or reproducer == red_actor:
            return Decision(
                False,
                "FINDING_NOT_REPRODUCED",
                f"{finding_id} was not reproduced independently of the Red operator",
            )
    return None


def evaluate(request: dict[str, Any], table: dict[str, Any]) -> Decision:
    """Evaluate one transition request against the declared table.

    The request is assumed to already validate against
    ``contracts/ticket-transition.schema.json``; this function checks the rules a
    schema cannot express.
    """
    source, target = request["from"], request["to"]
    if request.get("effect_class") == "EXTERNAL_WORLD":
        refusal = _check_external_effect(table, request)
        if refusal is not None:
            return refusal
    entry = _find(table, source, target)
    if entry is None:
        if _skipped(table, source, target):
            return Decision(
                False, "SKIPPED_STANDING", f"{source} -> {target} skips a declared standing"
            )
        return Decision(
            False, "UNKNOWN_TRANSITION", f"{source} -> {target} is not a declared transition"
        )
    if request["actor_kind"] not in entry["actor_kinds"]:
        return Decision(
            False,
            "ACTOR_KIND_REFUSED",
            f"actor_kind {request['actor_kind']} may not perform {source} -> {target}",
        )
    if entry.get("requires_owner") and request["actor_id"] not in table["owner_actor_ids"]:
        code = "OWNER_RATIFICATION_REQUIRED" if target == "RATIFIED" else "OWNER_JUDGEMENT_REQUIRED"
        return Decision(
            False, code, f"{source} -> {target} is owner judgement; {request['actor_id']} is not the owner"
        )
    missing = _missing_evidence(entry, request)
    if missing:
        return Decision(False, "MISSING_EVIDENCE", f"absent evidence: {', '.join(sorted(missing))}")
    if entry.get("requires_distinct_actor"):
        builder = request.get("builder_actor_id")
        if not builder:
            return Decision(
                False, "SELF_WITNESS_REFUSED", "the request names no builder actor to witness against"
            )
        if builder == request["actor_id"]:
            return Decision(
                False,
                "SELF_WITNESS_REFUSED",
                f"{request['actor_id']} built the artifact and may not witness it",
            )
    if entry.get("requires_purple"):
        refusal = _check_purple(request)
        if refusal is not None:
            return refusal
    return Decision(True, None, f"{source} -> {target} satisfies every declared precondition")
