"""Declare predicates before the looking, then observe a run by reading its outputs yourself.

`observe_run` is the service-owned path behind the kernel transition of the same name. It
reads the durable outputs through an injected reader, checks their bytes against the digests
the record declares, evaluates predicates that were declared beforehand, and returns an
`Observation` shaped by `contracts/observation.schema.json`. It settles nothing.

The predicate language is deliberately small and is a default taken (`decisions/0041`, Defaults
taken: "No predicate language is chosen"). Every kind reads bytes at an output address the run
reported and never the executor's report, which is what the manifest's precondition
`predicates_evaluable_without_executor_report` means here.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable
import hashlib
import json

from .errors import DigestMismatch, PredicatesUndeclared, Unreadable
from .record import RunRecord, digest_address
from .relation import require_independent

Reader = Callable[[str], bytes]

PREDICATE_KINDS = ("DIGEST_EQUALS", "BYTES_PRESENT", "JSON_FIELD_EQUALS")


def _moment(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise PredicatesUndeclared("a timestamp is absent")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise PredicatesUndeclared(f"unreadable timestamp {value!r}") from error


def declare_predicates(run_id: str, predicates: list[dict[str, Any]],
                       declared_at: str) -> dict[str, Any]:
    """Record what must hold, before anyone looks. Refuses an empty or unevaluable set."""
    if not predicates:
        raise PredicatesUndeclared("no predicate was declared")
    for entry in predicates:
        for field in ("predicate_id", "kind", "address"):
            if not entry.get(field):
                raise PredicatesUndeclared(f"a predicate omits {field}")
        if entry["kind"] not in PREDICATE_KINDS:
            raise PredicatesUndeclared(f"{entry['predicate_id']} uses unknown kind {entry['kind']}")
        if entry["kind"] == "DIGEST_EQUALS" and digest_address(entry.get("expected")) is None:
            raise PredicatesUndeclared(f"{entry['predicate_id']} expects no sha256 digest")
        if entry["kind"] == "JSON_FIELD_EQUALS" and not entry.get("field"):
            raise PredicatesUndeclared(f"{entry['predicate_id']} names no field")
    _moment(declared_at)
    material = f"{run_id}|{declared_at}|{json.dumps(predicates, sort_keys=True)}".encode("utf-8")
    return {
        "declaration_id": "urn:soveraeign:observation:predicates:"
                          + hashlib.sha256(material).hexdigest()[:24],
        "run_id": run_id,
        "predicates": [dict(entry) for entry in predicates],
        "declared_at": declared_at,
    }


def _evaluate(predicate: dict[str, Any], payload: bytes) -> bool:
    kind = predicate["kind"]
    if kind == "BYTES_PRESENT":
        return len(payload) > 0
    if kind == "DIGEST_EQUALS":
        actual = "sha256:" + hashlib.sha256(payload).hexdigest()
        return digest_address(predicate["expected"]) == actual
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return False
    if not isinstance(document, dict):
        return False
    return document.get(predicate["field"]) == predicate.get("expected")


def _read(reader: Reader, address: str) -> bytes:
    try:
        payload = reader(address)
    except Exception as error:  # the port may raise anything; every failure is UNREADABLE
        raise Unreadable(f"{address}: {error}") from error
    if not isinstance(payload, (bytes, bytearray)):
        raise Unreadable(f"{address} yielded no bytes")
    return bytes(payload)


def observe_run(
    record: RunRecord,
    inference: dict[str, Any],
    declaration: dict[str, Any],
    observer_id: str,
    reader: Reader,
    observed_at: str,
) -> dict[str, Any]:
    """Read the run's outputs yourself and evaluate the declared predicates against them.

    Refuses `OBSERVER_NOT_INDEPENDENT` and `RELATION_UNDETERMINED` from the inference,
    `PREDICATES_UNDECLARED` when the declaration is absent, later than the looking, about
    another run, or names an address the run did not report, `UNREADABLE` when an output cannot
    be read, and `DIGEST_MISMATCH` when the bytes disagree with the record.
    """
    require_independent(inference, observer_id)
    if not declaration or declaration.get("run_id") != record.run_id:
        raise PredicatesUndeclared(f"no declaration for {record.run_id}")
    if _moment(declaration.get("declared_at")) >= _moment(observed_at):
        raise PredicatesUndeclared("predicates were declared after the looking")
    predicates = declaration.get("predicates") or []
    if not predicates:
        raise PredicatesUndeclared("the declaration names no predicate")
    reported = record.reported_addresses()
    outputs = record.outputs()
    own_entries = record.run_entry_ids() | {record.run_id}
    for predicate in predicates:
        address = predicate["address"]
        if address in own_entries:
            raise PredicatesUndeclared(
                f"{predicate['predicate_id']} reads {address}, which is the run's own entry: "
                f"a predicate over the executor's report is not evaluable without it")
        if address not in reported or address not in outputs:
            raise PredicatesUndeclared(
                f"{predicate['predicate_id']} reads {address}, which the run did not report "
                f"as a recorded durable output")

    addresses = sorted({predicate["address"] for predicate in predicates})
    payloads: dict[str, bytes] = {}
    digests: list[str] = []
    for address in addresses:
        payload = _read(reader, address)
        digest = "sha256:" + hashlib.sha256(payload).hexdigest()
        declared = digest_address((outputs.get(address) or {}).get("payload", {}).get("digest"))
        if declared is None:
            raise Unreadable(f"the record declares no sha256 digest for {address}, so its bytes "
                             f"cannot be checked against anything")
        if declared != digest:
            raise DigestMismatch(f"{address} reads {digest} and the record declares {declared}")
        payloads[address] = payload
        digests.append(digest)

    results = {predicate["predicate_id"]: _evaluate(predicate, payloads[predicate["address"]])
               for predicate in predicates}
    material = f"{record.run_id}|{observer_id}|{'|'.join(addresses)}".encode("utf-8")
    return {
        "observation_id": "urn:soveraeign:observation:"
                          + hashlib.sha256(material).hexdigest()[:24],
        "run_id": record.run_id,
        "observer_id": observer_id,
        "observer_relation": (
            f"INDEPENDENT per {inference['inference_id']}: none of "
            f"{', '.join(inference['edges_examined'])} found over a COMPLETE record; "
            f"outputs read directly, not through the executor's report"),
        "observed_state_addresses": addresses,
        "observed_state_digests": digests,
        "predicate_results": results,
        "observed_at": observed_at,
    }


__all__ = ["PREDICATE_KINDS", "Reader", "declare_predicates", "observe_run"]
