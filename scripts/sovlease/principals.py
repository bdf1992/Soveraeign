"""One principal, one spelling on the lease.

The principal registry (`contracts/principals.json`) names a principal `principal:<id>`.
The lease contract names its holder `urn:soveraeign:principal:<kind>:<id>`. Both are
right for their own surface, and until now nothing owned the mapping between them, so a
holder typing the registry's name got a pattern error and guessed the URN
(`reports/2026-09-05-thin-circuit-1.md`, fizzle 1).

This module owns that mapping and nothing else. The kind comes from the registry, never
from the caller: `MODEL` becomes `model`, `HUMAN` becomes `human`. A name the registry
does not hold is refused rather than guessed, because a URN minted from an unregistered
name would read as an identity nothing ever declared; a name the registry has revoked is
refused for the same reason in the other direction.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sovsession import principals as registry

REGISTRY_PREFIX = "principal:"
URN_PREFIX = "urn:soveraeign:principal:"

UNREGISTERED_PRINCIPAL = "UNREGISTERED_PRINCIPAL"
"""The registry spelling names no registered principal; nothing can supply its kind."""

REVOKED_PRINCIPAL = "REVOKED_PRINCIPAL"
"""The registry spelling names a principal the registry has revoked."""


class PrincipalRefused(RuntimeError):
    """The registry spelling could not be mapped; the message opens with the reason code."""


class UnregisteredPrincipal(PrincipalRefused):
    """A `principal:<id>` the registry does not hold, or a registry that could not be read."""


class RevokedPrincipal(PrincipalRefused):
    """A `principal:<id>` whose registry entry carries `revoked`."""


def resolve(value: str, loaded: dict[str, Any]) -> str:
    """Map one spelling against an already-loaded registry.

    A value already in URN form passes through unchanged and unchecked: the contract's
    own pattern shapes it, an instance principal is minted per invocation rather than
    registered, and this function does not look a URN up, so a URN naming a revoked
    principal is not caught here. A value in the registry's `principal:<id>` spelling is
    mapped to `urn:soveraeign:principal:<kind>:<id>` with `<kind>` read from the
    registry and lowercased. Anything else is returned as typed and left to the contract
    to refuse.
    """
    if not value.startswith(REGISTRY_PREFIX):
        return value
    record = registry.index(loaded).get(value)
    if record is None:
        raise UnregisteredPrincipal(
            f"{UNREGISTERED_PRINCIPAL}: {value} is not in {registry.REGISTRY_PATH}; "
            f"a lease holder is either a registered principal or a full "
            f"{URN_PREFIX}<kind>:<id>")
    if record.get("revoked"):
        raise RevokedPrincipal(f"{REVOKED_PRINCIPAL}: {value} is revoked in "
                               f"{registry.REGISTRY_PATH} and cannot hold a lease")
    kind = str(record.get("kind") or "").lower()
    if not kind:
        raise UnregisteredPrincipal(f"{UNREGISTERED_PRINCIPAL}: {value} declares no kind in "
                                    f"{registry.REGISTRY_PATH}")
    return f"{URN_PREFIX}{kind}:{value[len(REGISTRY_PREFIX):]}"


def instance_principal(value: str, root: Path) -> str:
    """The URN the lease contract requires, reading the node's registry when needed.

    The registry is loaded only for the `principal:<id>` spelling; a URN never touches
    it. An absent or unreadable registry refuses the registry spelling rather than
    guessing a kind.
    """
    if not value.startswith(REGISTRY_PREFIX):
        return value
    loaded, reason = registry.load(root)
    if loaded is None:
        raise UnregisteredPrincipal(f"{UNREGISTERED_PRINCIPAL}: {value} cannot be resolved; "
                                    f"{reason}")
    return resolve(value, loaded)
