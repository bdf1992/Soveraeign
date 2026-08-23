"""The shared kernel: one object every service composes for its legal transitions."""

from __future__ import annotations

from .base import KernelBase
from .runs import RunTransitions
from .standing import StandingTransitions


class Kernel(StandingTransitions, RunTransitions, KernelBase):
    """Reference realization of the ``SPEC.md`` transition contract over one journal.

    Services hold a ``Kernel`` and call its transitions; they never append to the
    journal or edit a record directly. ``audit`` exposes a service that did.
    """
