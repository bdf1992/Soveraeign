"""Read-only Host Service participant over an injected Host Port."""

from __future__ import annotations

from typing import Any

from soveraeign_record_service import RecordService

from .ports import HostAdapterUnavailable, HostPort

EFFECT_CLASS = "RECORD_LOCAL"
EVENT = "host.read-health"
BOUNDARY = "PROCESS_EXECUTION_HOST"
SNAPSHOT_FIELDS = frozenset({
    "schema_version", "adapter_id", "captured_at", "boundary", "platform",
    "processor", "memory", "uptime_seconds", "boot_id", "limitations",
})


def _optional_number(value: Any) -> bool:
    return value is None or isinstance(value, (int, float)) and not isinstance(value, bool)


def _optional_integer(value: Any) -> bool:
    return value is None or isinstance(value, int) and not isinstance(value, bool)


def snapshot_defect(snapshot: Any, adapter_id: str) -> str | None:
    """Return the first contract defect without trusting an adapter self-report."""
    if not isinstance(snapshot, dict) or set(snapshot) != SNAPSHOT_FIELDS:
        return "snapshot fields do not match the Host Service contract"
    if snapshot.get("schema_version") != "soveraeign-host-health/v1":
        return "snapshot schema version is unknown"
    if snapshot.get("adapter_id") != adapter_id:
        return "snapshot adapter identity differs from the configured Host Port"
    if snapshot.get("boundary") != BOUNDARY:
        return "snapshot does not declare the process execution host boundary"
    if not isinstance(snapshot.get("captured_at"), str) or not snapshot["captured_at"]:
        return "snapshot capture time is absent"

    platform = snapshot.get("platform")
    if (not isinstance(platform, dict) or set(platform) != {"system", "release", "machine"}
            or any(not isinstance(platform[name], str)
                   for name in ("system", "release", "machine"))):
        return "platform reading has an invalid shape"
    processor = snapshot.get("processor")
    if (not isinstance(processor, dict)
            or set(processor) != {"logical_count", "load_average"}
            or not _optional_integer(processor["logical_count"])
            or processor["logical_count"] is not None and processor["logical_count"] < 1
            or (processor["load_average"] is not None
                and (not isinstance(processor["load_average"], list)
                     or len(processor["load_average"]) != 3
                     or any(not _optional_number(item)
                            or item is not None and item < 0
                            for item in processor["load_average"])))):
        return "processor reading has an invalid shape"
    memory = snapshot.get("memory")
    if (not isinstance(memory, dict) or set(memory) != {"total_bytes", "available_bytes"}
            or not _optional_integer(memory["total_bytes"])
            or not _optional_integer(memory["available_bytes"])
            or any(value is not None and value < 0 for value in memory.values())
            or (memory["total_bytes"] is not None and memory["available_bytes"] is not None
                and memory["available_bytes"] > memory["total_bytes"])):
        return "memory reading has an invalid shape"
    if (not _optional_number(snapshot.get("uptime_seconds"))
            or snapshot.get("uptime_seconds") is not None
            and snapshot["uptime_seconds"] < 0):
        return "uptime reading has an invalid shape"
    if (snapshot.get("boot_id") is not None
            and (not isinstance(snapshot["boot_id"], str) or not snapshot["boot_id"])):
        return "boot identity has an invalid shape"
    limitations = snapshot.get("limitations")
    if (not isinstance(limitations, list)
            or any(not isinstance(item, str) or not item for item in limitations)):
        return "limitations have an invalid shape"
    return None


class HostService:
    """Own Host readings and terminal receipts; never infer adapter authority."""

    def __init__(self, record: RecordService, adapter: HostPort, *,
                 host_id: str = "host:local") -> None:
        if not isinstance(host_id, str) or not host_id:
            raise ValueError("host_id must be a non-empty configured identity")
        self.record = record
        self.adapter = adapter
        self.host_id = host_id

    def _receipt(self, outcome: str, actor: str, detail: dict[str, Any]) -> dict[str, Any]:
        return self.record.receipt(
            outcome, EVENT, self.host_id, actor,
            {
                "effect_class": EFFECT_CLASS,
                "operation_type": EVENT,
                "host_id": self.host_id,
                **detail,
            },
        )

    def malformed_read_health(self, actor: str) -> dict[str, Any]:
        """Return the service-owned terminal refusal for an argument-shape defeat."""
        return self._receipt("REFUSED", actor, {"reason_code": "MALFORMED_HOST_REQUEST"})

    def read_health(self, actor: str) -> dict[str, Any]:
        """Read the configured execution boundary and append one terminal receipt."""
        try:
            snapshot = self.adapter.read_health()
        except HostAdapterUnavailable as error:
            return self._receipt("REFUSED", actor, {
                "reason_code": "HOST_UNAVAILABLE",
                "diagnostic": str(error),
            })
        except Exception as error:
            return self._receipt("FAILED", actor, {
                "reason_code": "HOST_READ_FAILED",
                "error_type": type(error).__name__,
                "diagnostic": str(error),
            })

        defect = snapshot_defect(snapshot, self.adapter.adapter_id)
        if defect:
            reason = ("HOST_BOUNDARY_UNKNOWN" if isinstance(snapshot, dict)
                      and (snapshot.get("boundary") != BOUNDARY
                           or snapshot.get("adapter_id") != self.adapter.adapter_id)
                      else "HOST_READ_FAILED")
            return self._receipt("REFUSED", actor, {
                "reason_code": reason,
                "diagnostic": defect,
            })
        return self._receipt("COMMITTED", actor, {
            "reason_code": None,
            "commit_semantics": "DERIVED",
            "standing_effect": "NONE",
            "observation_status": "UNATTESTED_ADAPTER_READING",
            "snapshot": snapshot,
        })


__all__ = ["BOUNDARY", "HostService", "snapshot_defect"]
