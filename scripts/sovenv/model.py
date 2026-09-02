"""Compatibility facade for non-authoritative Environment model operations.

Governed promotion admission is intentionally absent from this facade. Operational
callers use `sovenv.authority.admit_crossing`; focused state-machine tests may import
the raw transition from `sovenv.transitions` explicitly.
"""

from __future__ import annotations

from .errors import EnvironmentRefused
from .pattern import canonical, digest, load_json, validate_pattern
from .state import (
    bind_workspace,
    instantiate_environment,
    instantiate_trunk,
    new_state,
    release_workspace,
)
from .store import StateStore
from .transitions import land_crossing, propose_crossing, resolve_selector

__all__ = [
    "EnvironmentRefused",
    "StateStore",
    "bind_workspace",
    "canonical",
    "digest",
    "instantiate_environment",
    "instantiate_trunk",
    "land_crossing",
    "load_json",
    "new_state",
    "propose_crossing",
    "release_workspace",
    "resolve_selector",
    "validate_pattern",
]
