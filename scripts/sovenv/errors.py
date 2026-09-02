"""Shared refusal type for the local Environment reference vertical."""

from __future__ import annotations


class EnvironmentRefused(ValueError):
    """A requested local SDLC transition is not admissible."""
