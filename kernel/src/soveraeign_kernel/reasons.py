"""Refusal reason codes the shared kernel may place on a receipt.

The codes named in ``SPEC.md`` Transition contract are carried verbatim. The
remaining codes are proposals: ``SPEC.md`` allows a "reasoned refusal" without
naming the reason, and a refusal that cannot be named cannot be compared across
bindings. Each proposed code is marked so O10 can accept, rename, or strike it.
"""

from __future__ import annotations

# Named in SPEC.md.
STALE_STATE = "STALE_STATE"
INCOMPLETE_PROPOSAL = "INCOMPLETE_PROPOSAL"
ADMISSION_REFUSED = "ADMISSION_REFUSED"
AUTHORITY_REFUSED = "AUTHORITY_REFUSED"
VALIDATOR_UNDECLARED = "VALIDATOR_UNDECLARED"
DISSENTED = "DISSENTED"
UNATTESTABLE = "UNATTESTABLE"
POLICY_REFUSED = "POLICY_REFUSED"
STALE_LEASE = "STALE_LEASE"
OBSERVER_NOT_INDEPENDENT = "OBSERVER_NOT_INDEPENDENT"

# Proposed (not yet in SPEC.md; queued under O10).
INCOMPLETE_PLAN = "INCOMPLETE_PLAN"
EFFECT_CLASS_REFUSED = "EFFECT_CLASS_REFUSED"
STANDING_REFUSED = "STANDING_REFUSED"
OBSERVATION_MISSING = "OBSERVATION_MISSING"
TARGET_UNKNOWN = "TARGET_UNKNOWN"
PREDICATE_FAILED = "PREDICATE_FAILED"
PREDICATE_UNRESOLVED = "PREDICATE_UNRESOLVED"

SPEC_NAMED = frozenset({
    STALE_STATE, INCOMPLETE_PROPOSAL, ADMISSION_REFUSED, AUTHORITY_REFUSED,
    VALIDATOR_UNDECLARED, DISSENTED, UNATTESTABLE, POLICY_REFUSED, STALE_LEASE,
    OBSERVER_NOT_INDEPENDENT,
})

PROPOSED = {
    INCOMPLETE_PLAN: "a run was requested without a complete OperationPlan",
    EFFECT_CLASS_REFUSED: "the declared effect class is not admitted in this phase",
    STANDING_REFUSED: "the target record is not in the standing the transition requires",
    OBSERVATION_MISSING: "settlement was requested with no independent observation on record",
    TARGET_UNKNOWN: "the named record, run, or grant does not exist in this kernel",
    PREDICATE_FAILED: "settlement found an observed predicate false; the run FAILED",
    PREDICATE_UNRESOLVED: "an observed predicate has no result yet; the run is UNRESOLVED",
}

ALL = SPEC_NAMED | frozenset(PROPOSED)
