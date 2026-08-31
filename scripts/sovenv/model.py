"""Compatibility facade for the local Environment / Trunk / Deployment kernel."""

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
from .transitions import admit_crossing, land_crossing, propose_crossing, resolve_selector

__all__ = [
    "EnvironmentRefused",
    "StateStore",
    "admit_crossing",
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
