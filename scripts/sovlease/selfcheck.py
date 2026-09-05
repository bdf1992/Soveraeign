"""Prove the lease commands offline, without touching the repository's real store.

The unit tests judge records that were written by hand. This checks the other half: that
the construction path the command line actually uses produces a record the contract
accepts, that the projection replays events into current state without editing a line, and
that a helper built through that same path cannot be handed authority its parent lacks.
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
import json
import tempfile

from sovkernel import lease_budget
from sovkernel import work_lease
from sovkernel.jsonschema import validate
from sovlease import commands
from sovlease import principals
from sovlease import store
from sovsession import principals as registry

ROOT = Path(__file__).resolve().parents[2]


def _args(**overrides) -> Namespace:
    """The option set every lease-building command shares, with test values."""
    base = dict(
        concern_kind="ticket", reference="#1", capability_served=None,
        definition="sov-worker", definition_kind="agent", provenance="SYSTEM_AUTHORED",
        definition_version="1", derives_from=None, definition_source=None,
        grant=None, authority_type=None, capability=None, effect_ceiling="RECORD_LOCAL",
        budget=["tokens=1000"], emit=["helper_leases=2"], minutes=60,
        closure="it lands", defeat="it does not land", principal=None, cleanup=None,
    )
    base.update(overrides)
    return Namespace(**base)


def _schema() -> dict:
    with (ROOT / commands.CONTRACT).open(encoding="utf-8") as handle:
        return json.load(handle)


def _check_construction(failures: list[str]) -> dict:
    """A lease built the way the command line builds it satisfies the contract."""
    lease = commands._build(_args(), "lease:selfcheck", "session-selfcheck",
                            "PARENT", None, "urn:soveraeign:principal:human:bdo", 1, ROOT)
    defects = validate(lease, _schema())
    if defects:
        failures.append("a lease built by the command path is refused by its own "
                        "contract: " + "; ".join(defects))
    return lease


def _check_no_authority_minting(parent: dict, failures: list[str]) -> None:
    """A helper cannot be handed a capability the parent does not hold."""
    parent = dict(parent)
    parent["grant"] = {"grant_id": "grant:read", "authority_type": "VERIFICATION",
                       "capabilities": ["asset.read"], "effect_ceiling": "RECORD_LOCAL"}
    helper = commands._build(
        _args(grant="grant:minted", authority_type="VERIFICATION",
              capability=["asset.read", "asset.retract"], minutes=30),
        "lease:selfcheck-helper", "session-selfcheck", "HELPER", parent["lease_id"],
        parent["holder"]["principal_id"], 1, ROOT)
    codes = {defect.code for defect in work_lease.evaluate(helper, parent=parent)}
    if "AUTHORITY_WIDENED" not in codes:
        failures.append("a helper built with more than its parent holds was admitted")


def _check_projection(lease: dict, failures: list[str]) -> None:
    """Replaying the log yields current state, and closing never rewrites a line."""
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        store.append(directory, store.LEASES_LOG,
                     {"event": "take", "lease_id": lease["lease_id"], "lease": lease})
        store.append(directory, store.LEASES_LOG,
                     {"event": "release", "lease_id": lease["lease_id"]})
        projected = store.leases(directory)[lease["lease_id"]]
        if projected["state"] != "RELEASED":
            failures.append(f"projection read {projected['state']}, expected RELEASED")
        lines = (directory / store.LEASES_LOG).read_text(encoding="utf-8").splitlines()
        if len(lines) != 2:
            failures.append(f"the log holds {len(lines)} lines; a release must add an "
                            f"event, never edit the take")
        if store.next_fence({lease["lease_id"]: projected}, lease["lease_id"]) != 2:
            failures.append("the next fence did not supersede the current one")


def _check_budget(lease: dict, failures: list[str]) -> None:
    """An overdrawn envelope reads as overdrawn."""
    draws = [{"lease_id": lease["lease_id"], "kind": "consumption",
              "dimension": "tokens", "amount": 1500}]
    codes = {reading["code"] for reading in lease_budget.readings(lease, draws)}
    if "BUDGET_EXCEEDED" not in codes:
        failures.append("a draw past a declared limit produced no reading")


def _check_principal_spelling(failures: list[str]) -> None:
    """Both spellings of one principal reach the contract; an unregistered one does not.

    The registry's root principal is read back from the registry rather than assumed, so
    this check keeps grading the live file if that principal is ever renamed.
    """
    loaded, reason = registry.load(ROOT)
    if loaded is None:
        failures.append("the principal registry could not be read: " + reason)
        return
    root_id = loaded.get("root_principal")
    kind = str(registry.index(loaded)[root_id]["kind"]).lower()
    expected = principals.URN_PREFIX + kind + ":" + root_id.removeprefix("principal:")
    lease = commands._build(_args(principal=root_id), "lease:selfcheck-spelling",
                            "session-selfcheck", "PARENT", None, None, 1, ROOT)
    if lease["holder"]["principal_id"] != expected:
        failures.append(f"{root_id} mapped to {lease['holder']['principal_id']}, "
                        f"expected {expected}")
    if validate(lease, _schema()):
        failures.append("the mapped principal does not satisfy the contract")
    if principals.instance_principal(expected, ROOT) != expected:
        failures.append("a principal already in URN form did not pass through unchanged")
    try:
        principals.instance_principal("principal:nobody-registered-this", ROOT)
    except principals.UnregisteredPrincipal as refusal:
        if principals.UNREGISTERED_PRINCIPAL not in str(refusal):
            failures.append("the unregistered refusal does not name its reason")
    else:
        failures.append("an unregistered principal: spelling was mapped instead of refused")
    # The live registry revokes nobody, so the revoked refusal is reached on a hand-built
    # one; the same id with revoked cleared must map, or the check is grading the id.
    revoked = {"principals": [{"principal_id": "principal:gone", "kind": "MODEL",
                               "revoked": {"at": "2026-09-05T00:00:00Z"}}]}
    try:
        principals.resolve("principal:gone", revoked)
    except principals.RevokedPrincipal as refusal:
        if principals.REVOKED_PRINCIPAL not in str(refusal):
            failures.append("the revoked refusal does not name its reason")
    else:
        failures.append("a revoked principal: spelling was mapped instead of refused")
    revoked["principals"][0]["revoked"] = None
    if principals.resolve("principal:gone", revoked) != principals.URN_PREFIX + "model:gone":
        failures.append("the same id with revoked cleared did not map")


def _check_cleanup_obligations(failures: list[str]) -> None:
    """Obligations land under closure, and a wordless one is refused by the contract."""
    lease = commands._build(_args(cleanup=["release the lease"]), "lease:selfcheck-cleanup",
                            "session-selfcheck", "PARENT", None, None, 1, ROOT)
    if lease["closure"].get("cleanup_obligations") != ["release the lease"]:
        failures.append("--cleanup did not land under closure.cleanup_obligations")
    if validate(lease, _schema()):
        failures.append("a lease with a cleanup obligation is refused by its contract")
    empty = commands._build(_args(cleanup=[""]), "lease:selfcheck-cleanup",
                            "session-selfcheck", "PARENT", None, None, 1, ROOT)
    if not validate(empty, _schema()):
        failures.append("an empty-string cleanup obligation was admitted by the contract")


def run() -> int:
    """Every offline check, reporting each failure rather than the first."""
    failures: list[str] = []
    lease = _check_construction(failures)
    _check_no_authority_minting(lease, failures)
    _check_projection(lease, failures)
    _check_budget(lease, failures)
    _check_principal_spelling(failures)
    _check_cleanup_obligations(failures)
    if failures:
        for failure in failures:
            print("FAIL: " + failure)
        return 1
    print("PASS: lease construction, projection, budget, subordination, principal "
          "spelling and cleanup-obligation checks")
    return 0
