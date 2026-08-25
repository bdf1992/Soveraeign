"""Read-only standard-library adapter for the local process execution host."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import os
import platform

ADAPTER_ID = "urn:soveraeign:adapter:local-host-stdlib:v1"
BOUNDARY = "PROCESS_EXECUTION_HOST"


def _read_text(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None


def _linux_memory() -> dict[str, int | None]:
    content = _read_text("/proc/meminfo")
    values: dict[str, int] = {}
    if content:
        for line in content.splitlines():
            name, separator, remainder = line.partition(":")
            fields = remainder.strip().split()
            if separator and fields and fields[0].isdigit():
                multiplier = 1024 if len(fields) > 1 and fields[1] == "kB" else 1
                values[name] = int(fields[0]) * multiplier
    return {
        "total_bytes": values.get("MemTotal"),
        "available_bytes": values.get("MemAvailable"),
    }


def _uptime() -> float | None:
    content = _read_text("/proc/uptime")
    if not content:
        return None
    try:
        return float(content.split()[0])
    except (IndexError, ValueError):
        return None


class LocalHostAdapter:
    """Translate OS readings without shell execution, mutation, or elevation."""

    adapter_id = ADAPTER_ID

    def read_health(self) -> dict[str, Any]:
        limitations = [
            "boundary_is_process_execution_host_not_verified_physical_machine",
            "adapter_reading_is_not_independent_observation",
        ]
        memory = _linux_memory()
        if memory["total_bytes"] is None:
            limitations.append("memory_total_unavailable")
        if memory["available_bytes"] is None:
            limitations.append("memory_available_unavailable")

        uptime = _uptime()
        if uptime is None:
            limitations.append("uptime_unavailable")
        boot_id = _read_text("/proc/sys/kernel/random/boot_id")
        if boot_id is None:
            limitations.append("boot_id_unavailable")
        try:
            load_average: list[float] | None = [float(value) for value in os.getloadavg()]
        except (AttributeError, OSError):
            load_average = None
            limitations.append("load_average_unavailable")
        logical_count = os.cpu_count()
        if logical_count is None:
            limitations.append("logical_processor_count_unavailable")

        return {
            "schema_version": "soveraeign-host-health/v1",
            "adapter_id": self.adapter_id,
            "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "boundary": BOUNDARY,
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
            },
            "processor": {
                "logical_count": logical_count,
                "load_average": load_average,
            },
            "memory": memory,
            "uptime_seconds": uptime,
            "boot_id": boot_id,
            "limitations": sorted(set(limitations)),
        }


__all__ = ["ADAPTER_ID", "LocalHostAdapter"]
