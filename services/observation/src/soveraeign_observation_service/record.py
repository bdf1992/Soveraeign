"""Read a run's record the only way this service may: as Record Service journal entries.

The Record Service owns the journal and this service never writes it. An entry arrives in the
Record Service's own shape - `entry_id`, `kind`, `subject`, `actor`, `payload`, `entry_digest` -
so a journal read, or a projection rebuilt from one, feeds the inference directly. Nothing here
imports the Record Service: the boundary is the entry shape, not the code.

Six payload events are read. They are the record's own words, written by the kernel
transitions `SPEC.md` names, and the inference in `relation.py` trusts nothing else:

- `ATTEMPTED` on the run subject: `begin_run` happened. The entry's actor is the executor;
  the payload carries `lease` (an object or null) and `grant_id` (a string or null). A key that
  is absent is a question the record cannot answer, which is different from a null answer.
- `REPORTED` on the run subject: `report_run` happened. The payload names
  `output_record_addresses`, what the executor says it produced.
- `OUTPUT` on an output address: a durable output exists. Its actor produced it and its
  payload carries the `digest` a reader can check the bytes against.
- `GRANT` on a grant id: `holder_id` and `parent_grant_id` (null at the root). Kept because a
  reader may still want the chain; `decisions/0104` retired it as an independence edge.
- `LAUNCH` on a launched actor: `launched_actor_id`, `launched_by`, `context_passed` (the
  declared kinds of context handed over), `profile` (the operating profile the actor loaded,
  as address and digest), and `predicates_source_actor` (who authored the criteria it grades
  against). The launcher declares this, never the observer, so no participant vouches for
  itself. A launch entry that omits a key is a question the record cannot answer.
- `STANDING` on a work subject: `from` and `to`, the standing arrow this entry moved. Its
  actor is who moved it. These are what makes the walk lifecycle-wide rather than per-run.

Context kinds split in two. `CONSTRUCTION` kinds are what the run's own construction
produced; holding any one of them is the context edge. Everything else is subject-side and
carries no edge: an observer is meant to hold the objective and the artifact.

Terminal, for observation, means the run is no longer in flight: the executor has reported,
or a terminal receipt refused or settled it. Settlement is not required, because `settle_run`
refuses `OBSERVATION_MISSING` until an observation exists; a settled run may still be observed
later, which is what `counter-observation` is for. That reading is a default taken and is
recorded in `KNOWN-GAPS.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ATTEMPTED = "ATTEMPTED"
REPORTED = "REPORTED"
OUTPUT = "OUTPUT"
GRANT = "GRANT"
LAUNCH = "LAUNCH"
STANDING = "STANDING"

#: Context kinds a run's own construction produces. Holding one is not independence.
CONSTRUCTION_CONTEXT = frozenset({"REASONING", "PLAN", "TRANSCRIPT", "CONCLUSION"})

#: Events kept regardless of subject, because the walk reads them across the lifecycle.
CROSS_SUBJECT = (OUTPUT, GRANT, LAUNCH, STANDING)

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
            if entry.get("subject") == run_id or _event(entry) in CROSS_SUBJECT
        )
        return cls(run_id=run_id, entries=kept)

    def _run_events(self, event: str) -> list[dict[str, Any]]:
        return [entry for entry in self.entries
                if entry.get("subject") == self.run_id and entry.get("kind") == "EVENT"
                and _event(entry) == event]

    def malformed(self) -> str | None:
        """The first entry this service cannot read as a journal entry, or None.

        Every entry needs a kind, a subject, an address, and a sha256 digest; every entry on
        the run needs an actor, because an anonymous attempt or report would hide an executor.
        """
        for entry in self.entries:
            address = self.address_of(entry)
            if not isinstance(entry.get("payload"), dict):
                return f"entry {address} carries no payload object"
            for field in ("kind", "subject", "entry_id"):
                if not entry.get(field):
                    return f"entry {address} has no {field}"
            if digest_address(entry.get("entry_digest")) is None:
                return f"entry {address} carries no sha256 digest"
            if entry.get("subject") == self.run_id and not entry.get("actor"):
                return f"entry {address} on the run names no actor"
            if _event(entry) == STANDING and not entry.get("actor"):
                return f"standing entry {address} names no actor"
        return None

    def subject_id(self) -> str | None:
        """The standing subject the run declares, or None when it declares none.

        The lifecycle walk needs a subject to walk. A run that does not name one leaves that
        edge unanswerable, which refuses; it never reads as independence.
        """
        for attempt in self.attempts():
            named = (attempt.get("payload") or {}).get("subject_id")
            if named:
                return str(named)
        return None

    def launches(self) -> dict[str, dict[str, Any]]:
        """Launched actor -> the `LAUNCH` entry the launcher wrote about handing it context."""
        found: dict[str, dict[str, Any]] = {}
        for entry in self.entries:
            if _event(entry) != LAUNCH:
                continue
            actor = (entry.get("payload") or {}).get("launched_actor_id")
            if actor and str(actor) not in found:
                found[str(actor)] = entry
        return found

    def standings(self, subject_id: str) -> list[dict[str, Any]]:
        """Every `STANDING` arrow recorded on one subject, in append order."""
        return [entry for entry in self.entries
                if _event(entry) == STANDING and entry.get("subject") == subject_id]

    def profile_of(self, actor: str) -> str | None:
        """The digest of the operating profile an actor loaded, from a launch or an attempt.

        Perspective is carried by the profile, not by the actor id: a rename defeats an id and
        does not defeat a frame (`decisions/0104`, Ruling 3).
        """
        launch = self.launches().get(actor)
        if launch is not None:
            profile = (launch.get("payload") or {}).get("profile")
            if isinstance(profile, dict) and profile.get("digest"):
                return digest_address(profile["digest"])
        for entry in self.attempts() + self._run_events(REPORTED):
            if entry.get("actor") != actor:
                continue
            profile = (entry.get("payload") or {}).get("profile")
            if isinstance(profile, dict) and profile.get("digest"):
                return digest_address(profile["digest"])
        return None

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


__all__ = ["ATTEMPTED", "CONSTRUCTION_CONTEXT", "GRANT", "LAUNCH", "OUTPUT", "REPORTED",
           "STANDING", "RunRecord", "digest_address"]
