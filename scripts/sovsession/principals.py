"""Which principal a session is speaking as, read from the principal registry.

The registry names a session; it never authenticates one. A session is identified when a
registered principal matches it and unidentified otherwise, and the strength of that
identity is whatever the registry's own claim records. Nothing here upgrades a claim:
`UNVERIFIED` becomes `VERIFIED` only by presenting a live challenge token, which is the
Identity Service's lifecycle and not this module's (`decisions/0048`, ID-12 to ID-14).

Reporting a stronger identity than the record supports is the failure worth preventing, so
a claim that says `VERIFIED` without naming what verified it is reported as `UNVERIFIED`
with the defect stated, rather than believed.

The registry is a projection: being registered grants nothing (`decisions/0048`, ID-8).
Hop distance from the root is derived by walking controller edges and is deliberately not
stored (ID-3).

The instance does not exist in this branch yet. Until it does, every session resolves
`UNIDENTIFIED` and says which file it looked for, which is the honest reading of a node
that has not written its registry down.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os

REGISTRY_PATH = "contracts/principals.json"
"""Where the registry instance lives, beside the schema that shapes it."""

ENV_REGISTRY = "SOV_PRINCIPAL_REGISTRY"
ENV_PRINCIPAL = "SOV_PRINCIPAL"

UNIDENTIFIED = "UNIDENTIFIED"
"""No registered principal matches this session. Not a claim; the absence of one."""

UNVERIFIED = "UNVERIFIED"
VERIFIED = "VERIFIED"
REVOKED = "REVOKED"

MAX_CHAIN = 32
"""A control chain longer than this is treated as a cycle rather than walked further."""


def registry_path(root: Path) -> Path:
    """The registry file this node reads, overridable for a test or a second node."""
    override = os.environ.get(ENV_REGISTRY, "").strip()
    return Path(override) if override else root / REGISTRY_PATH


def _shown(root: Path, path: Path) -> str:
    """The registry path as a reader would name it: relative to the node when it is inside it.

    The briefing this reaches lands in every session's context, and an absolute temporary
    path is three lines of noise where `contracts/principals.json` is the whole answer.
    """
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def load(root: Path) -> tuple[dict[str, Any] | None, str]:
    """The registry, or None and the reason it could not be read.

    An absent file and an unreadable one are different answers. The first is a node that
    has not written its registry; the second is a defect, and saying `UNIDENTIFIED` for
    both would hide it.
    """
    path = registry_path(root)
    shown = _shown(root, path)
    if not path.is_file():
        return None, f"no principal registry at {shown}"
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as failure:
        return None, f"principal registry at {shown} could not be read: {failure}"
    if not isinstance(record, dict) or not isinstance(record.get("principals"), list):
        return None, f"principal registry at {shown} is not a registry"
    return record, ""


def index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """principal_id -> principal record."""
    return {item.get("principal_id"): item for item in registry.get("principals", [])
            if isinstance(item, dict) and item.get("principal_id")}


def chain(registry: dict[str, Any], principal_id: str) -> tuple[list[str], list[str]]:
    """The control chain from a principal up to the root, and any defect that broke it.

    Walking stops at the declared root, at an unknown controller, or at a repeat, and each
    of those is reported rather than swallowed: an unresolvable chain means the hop
    distance is unknown, which is a different answer from zero.
    """
    principals = index(registry)
    root = registry.get("root_principal")
    walked, seen, defects = [], set(), []
    current = principal_id
    while current is not None:
        if current in seen:
            defects.append(f"control chain revisits {current}")
            break
        if len(walked) > MAX_CHAIN:
            defects.append(f"control chain from {principal_id} exceeds {MAX_CHAIN} links")
            break
        record = principals.get(current)
        if record is None:
            defects.append(f"controller {current} is not a registered principal")
            break
        seen.add(current)
        walked.append(current)
        if record.get("revoked") and current != principal_id:
            defects.append(f"control chain passes through revoked principal {current}")
            break
        if current == root:
            break
        current = record.get("controller")
    if not defects and (not walked or walked[-1] != root):
        defects.append(f"control chain from {principal_id} does not reach the root {root}")
    return walked, defects


def _verification(record: dict[str, Any]) -> tuple[str, list[str]]:
    """What the registry's claim actually supports, and where it overstates itself."""
    if record.get("revoked"):
        return REVOKED, []
    claim = record.get("claim") or {}
    stated = claim.get("verification")
    if stated == VERIFIED:
        if not claim.get("verification_basis"):
            return UNVERIFIED, ["claim states VERIFIED but names no verification_basis"]
        if not record.get("verification_channel"):
            return UNVERIFIED, ["claim states VERIFIED but declares no verification channel"]
        return VERIFIED, []
    if stated == UNVERIFIED:
        return UNVERIFIED, []
    return UNVERIFIED, [f"claim states an unknown verification {stated!r}"]


def _blank(session: str, reason: str, registry: Path | None = None,
           root: Path | None = None) -> dict[str, Any]:
    """The record for a session no principal claims."""
    return {"session": session, "principal": None, "kind": None,
            "verification": UNIDENTIFIED, "controller": None, "hops": None,
            "root": None, "basis": reason, "defects": [],
            "registry": _shown(root, registry) if registry and root else None}


def candidate_ids(session: str) -> list[str]:
    """The principal ids that would name this session, most explicit first."""
    override = os.environ.get(ENV_PRINCIPAL, "").strip()
    names = [override] if override else []
    names.append(session if session.startswith("principal:") else f"principal:{session}")
    return names


def resolve(root: Path, session: str) -> dict[str, Any]:
    """This session's principal claim, as the registry records it and no stronger."""
    registry, reason = load(root)
    if registry is None:
        return _blank(session, reason)
    principals = index(registry)
    for candidate in candidate_ids(session):
        record = principals.get(candidate)
        if record is None:
            continue
        verification, defects = _verification(record)
        walked, chain_defects = chain(registry, candidate)
        claim = record.get("claim") or {}
        return {
            "session": session,
            "principal": candidate,
            "kind": record.get("kind"),
            "verification": verification,
            "controller": record.get("controller"),
            "hops": (len(walked) - 1) if not chain_defects else None,
            "root": registry.get("root_principal"),
            "basis": claim.get("claim_basis", ""),
            "defects": defects + chain_defects,
            "registry": _shown(root, registry_path(root)),
        }
    looked = ", ".join(candidate_ids(session))
    return _blank(session, f"no registered principal named {looked}",
                  registry_path(root), root)


def render(claim: dict[str, Any]) -> str:
    """One line naming who a session speaks as, and how strongly."""
    if claim["principal"] is None:
        return f"principal: unidentified - {claim['basis']}"
    hops = "unknown hops from the root" if claim["hops"] is None else (
        "the root" if claim["hops"] == 0 else
        f"{claim['hops']} hop{'' if claim['hops'] == 1 else 's'} from {claim['root']}")
    line = f"principal: {claim['principal']} ({claim['kind']}), {claim['verification']}, {hops}"
    if claim["defects"]:
        line += "; " + "; ".join(claim["defects"])
    return line
