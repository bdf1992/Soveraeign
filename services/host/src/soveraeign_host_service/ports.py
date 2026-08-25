"""Host Port contract supplied to the Host Service by a named adapter."""

from __future__ import annotations

from typing import Any, Protocol


class HostAdapterUnavailable(RuntimeError):
    """The configured adapter cannot currently read its execution boundary."""


class HostPort(Protocol):
    """The read-only port needed by the first Host Service slice."""

    adapter_id: str

    def read_health(self) -> dict[str, Any]:
        """Return one normalized execution-host health snapshot."""


__all__ = ["HostAdapterUnavailable", "HostPort"]
