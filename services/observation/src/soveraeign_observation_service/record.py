"""Read a run's record the only way this service may: as Record Service journal entries.

The Record Service owns the journal and this service never writes it. An entry arrives in the
Record Service's own shape - `entry_id`, `kind`, `subject`, `actor`, `payload`, `entry_digest` -
so a journal read, or a projection rebuilt from one, feeds the inference directly. Nothing here
imports the Record Service: the boundary is the entry shape, not the code.

Four payload events are read. They are the run's own words about itself, written by the
kernel transitions `SPEC.md` names, and the inference in `relation.py` trusts nothing else:

- `ATTEMPTED` on the run subject: `begin_run` happened. The entry's actor is the executor;
  the payload carries `lease` (an object or null) and `grant_id` (a string or null). A key that
  is absent is a question the record cannot answer, which is different from a null answer.
- `REPORTED` on the run subject: `report_run` happened. The payload names
  `output_record_addresses`, what the executor says it produced.
- `OUTPUT` on an output address: a durable output exists. Its actor produced it and its
  payload carries the `digest` a reader can check the bytes against.
- `GRANT` on a grant id: `holder_id` and `parent_grant_id` (null at the root), so a grant chain
  can be walked from the record rather than from anyone's say-so.

Terminal, for observation, means the executor has reported or the run refused. Settlement comes
after observation (`settle_run` refuses `OBSERVATION_MISSING`), so a run that had already
settled could never be observed. That reading is a default taken and is recorded in
`KNOWN-GAPS.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ATTEMPTED = "ATTEMPTED"
REPORTED = "REPORTED"
OUTPUT = "OUTPUT"
GRANT = "GRANT"

#: Receipt outcomes under which a run is no longer in flight.
TERMINAL_OUTCOMES = frozenset({"COMMITTED", "REFUSED", "FAILED", "COUNTERED", "UNRESOLVED"})


def _event(entry: dict[str, Any]) -> str | None:
    payload = entry.get("payload")
    return payload.get("event") if isinstance(payload, dict) else None


def digest_address(value: Any) -> str | None:
    """Normalise a digest to the `sha256:<hex>` form the kernel observation schema expects."""
    if not isinstance(value, str):
        return None
    hexdigest = value[7:] if value.startswith("sha256:") else value
    if len(hexdigest) != 64 or any(char not in "0123456789abcdef" for char in hexdigest):
        return None
    return f"sha256:{hexdigest}"


@dataclass(frozen=True)
class RunRecord:
    """One run's slice of the journal, in append order, read-only."""

    run_id: str
    entries: tuple[dict[str, Any], ...]

    @classmethod
    def from_entries(cls, run_id: str, entries: list[dict[str, Any]]) -> "RunRecord":
        """Keep the run's own entries plus every output and grant entry the walk may need."""
        kept = tuple(
            dict(entry) for entry in entries
            if entry.get("subject") == run_id or _event(entry) in (OUTPUT, GRANT)
        )
        return cls(run_id=run_id, entries=kept)

    def _run_events(self, event: str) -> list[dict[str, Any]]:
        return [entry for entry in self.entries
                if entry.get("subject") == self.run_id and entry.get("kind") == "EVENT"
                and _event(entry) == event]

    def attempts(self) -> list[dict[str, Any]]:
        """Every `ATTEMPTED` entry on the run. A second attempt has an executor too."""
        return self._run_events(ATTEMPTED)

    def attempt(self) -> dict[str, Any] | None:
        """The first `ATTEMPTED` entry; `attempts()` carries the rest."""
        found = self.attempts()
        return found[0] if found else None

    def executors(self) -> dict[str, dict[str, Any]]:
        """Actor -> the entry that shows them executing or reporting this run.

        The executor is whoever attempted the run and whoever reported it. The kernel refuses
        the reporter as observer (`transitions.py`, `reporter_id`), so this service must read
        the reporter as an executor or be weaker than the boundary it feeds.
        """
        seen: dict[str, dict[str, Any]] = {}
        for entry in self.attempts() + self._run_events(REPORTED):
            actor = str(entry.get("actor") or "")
            if actor and actor not in seen:
                seen[actor] = entry
        return seen

    def run_entry_ids(self) -> set[str]:
        """Addresses of the run's own entries; a predicate over one reads the run's word."""
        return {str(entry.get("entry_id")) for entry in self.entries
                if entry.get("subject") == self.run_id and entry.get("entry_id")}

    def report(self) -> dict[str, Any] | None:
        """The executor's `REPORTED` entry, the last if the record holds several."""
        found = self._run_events(REPORTED)
        return found[-1] if found else None

    def outputs(self) -> dict[str, dict[str, Any]]:
        """Output address -> the `OUTPUT` entry that records it."""
        return {str(entry.get("subject")): entry for entry in self.entries
                if entry.get("kind") == "EVENT" and _event(entry) == OUTPUT
                and entry.get("subject")}

    def grants(self) -> dict[str, dict[str, Any]]:
        """Grant id -> the `GRANT` entry that records it."""
        return {str(entry.get("subject")): entry for entry in self.entries
                if entry.get("kind") == "EVENT" and _event(entry) == GRANT
                and entry.get("subject")}

    def reported_addresses(self) -> list[str]:
        """What the executor says it produced; empty when nothing was reported."""
        report = self.report()
        if report is None:
            return []
        addresses = report.get("payload", {}).get("output_record_addresses")
        return [str(address) for address in addresses] if isinstance(addresses, list) else []

    def terminal_receipt(self) -> dict[str, Any] | None:
        """The last terminal RECEIPT on the run, if the kernel has written one."""
        found = [entry for entry in self.entries
                 if entry.get("subject") == self.run_id and entry.get("kind") == "RECEIPT"
                 and isinstance(entry.get("payload"), dict)
                 and entry["payload"].get("outcome") in TERMINAL_OUTCOMES]
        return found[-1] if found else None

    def terminal_outcome(self) -> str:
        """What the record says the run's terminal is.

        A receipt's outcome when one exists. A run that has only reported has not settled,
        and this service never reads the executor's report as settlement, so it records
        `UNRESOLVED`: the one terminal word that claims nothing was decided.
        """
        receipt = self.terminal_receipt()
        if receipt is not None:
            return str(receipt["payload"]["outcome"])
        return "UNRESOLVED"

    def is_terminal(self) -> bool:
        """Reported, or refused by a terminal receipt on the run."""
        return self.report() is not None or self.terminal_receipt() is not None

    @staticmethod
    def address_of(entry: dict[str, Any]) -> str:
        """The address an inference cites for an entry it read."""
        return str(entry.get("entry_id") or entry.get("subject"))

    @staticmethod
    def digest_of(entry: dict[str, Any]) -> str:
        """The entry digest in the form the observation schema requires."""
        digest = digest_address(entry.get("entry_digest"))
        if digest is None:
            raise ValueError(f"entry {RunRecord.address_of(entry)} carries no sha256 digest")
        return digest


__all__ = ["ATTEMPTED", "GRANT", "OUTPUT", "REPORTED", "RunRecord", "digest_address"]
