"""Judge the manifest before any store opens.

`gateway.py` owns the one path a call takes. This module owns the question asked
before any call is possible: does what the manifest declares line up with what this
binding can actually serve. It is a separate responsibility and a separate moment -
it runs at construction, touches no state, and a refusal here costs no file handle
and creates no state directory.

The vocabulary lives here too, because it is what the judgement is made against:
which tiers exist, which authority modes an acting endpoint may declare, and which
endpoint names this binding has code behind.
"""

from __future__ import annotations

from typing import Any

TIERS = ("read", "observe", "act")
AUTHORITY_MODES = ("gateway", "service-enforced", "bootstrap")

# The endpoints this gateway can actually reach. Held as names rather than bound
# callables so a manifest can be judged before anything opens a store: a refused
# start costs no file handle and creates no state directory.
IMPLEMENTED = (
    "authority_open_session",
    "authority_grant",
    "asset_ingest",
    "asset_search",
    "record_entries",
    "console_operations",
    "observe_verify",
)


class UnbuiltEndpoint(RuntimeError):
    """A manifest endpoint names an operation with no reachable implementation."""


def validate(endpoints: dict[str, dict[str, Any]],
              withheld: dict[str, dict[str, Any]] | None = None) -> None:
    """Judge the manifest before any store opens.

    A declared operation with nothing behind it is the failure this exists for:
    it keeps a written-but-unbuilt service visibly unbuilt instead of letting it
    become a tool that errors at call time.

    The reverse - an implementation the manifest does not declare - is normally the
    same defect read from the other side, and is admitted only when the manifest
    withholds that tool and says why. Withholding is how a built endpoint stops
    being served without the code that serves it being deleted, and a withheld
    entry with no stated reason is refused so a capability cannot quietly vanish.
    """
    withheld = withheld or {}
    missing = sorted(set(endpoints) - set(IMPLEMENTED))
    if missing:
        raise UnbuiltEndpoint(
            "manifest declares endpoints with no implementation: " + ", ".join(missing))
    for tool, entry in sorted(withheld.items()):
        if tool in endpoints:
            raise UnbuiltEndpoint(f"{tool} is both declared and withheld")
        if not entry.get("withheld_because"):
            raise UnbuiltEndpoint(f"{tool} is withheld without a stated reason")
    undeclared = sorted(set(IMPLEMENTED) - set(endpoints) - set(withheld))
    if undeclared:
        raise UnbuiltEndpoint(
            "gateway implements endpoints the manifest neither declares nor withholds: "
            + ", ".join(undeclared))
    for tool, entry in endpoints.items():
        if entry["tier"] not in TIERS:
            raise UnbuiltEndpoint(f"{tool} declares unknown tier {entry['tier']!r}")
        caller = entry.get("caller_argument")
        if caller is not None and caller in entry.get("arguments", {}):
            # Declaring it as an input invites a caller to send one, and a reader of
            # the tool schema would believe it decides something. The dispatcher
            # overwrites it, so the two together would be a contradiction on the wire.
            raise UnbuiltEndpoint(
                f"{tool} declares {caller!r} as an argument and as its caller_argument")
        if entry["tier"] != "act":
            continue
        mode = entry.get("authority")
        if mode not in AUTHORITY_MODES:
            raise UnbuiltEndpoint(f"{tool} acts but declares no authority mode")
        if (mode == "gateway") != ("capability" in entry):
            raise UnbuiltEndpoint(
                f"{tool} declares authority {mode!r}, which does not match its capability")
