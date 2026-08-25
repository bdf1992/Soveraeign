"""Checks that decide whether one Model Binding and one invocation record are admissible.

The adapter translates a Soveraeign Model Binding to a locally hosted Ollama-compatible
runtime. It holds no authority, settles nothing, and writes no authoritative state; it
decides only whether a declared binding matches the runtime that was actually recorded,
and whether an invocation record accounts for what actually ran.

Every check reads ``inventory.json`` rather than the live runtime. A tag is not custody:
the recorded inventory carries two models whose declared family, size, quantisation, and
context length are identical and which differ only in ``remote_host``. A check that
trusted the tag would admit a binding that sends the input off the machine under a
``LOCAL_ONLY`` data boundary.

Refusal reason codes: ``MODEL_UNAVAILABLE``, ``MODEL_INCOMPATIBLE``, and
``DATA_BOUNDARY_REFUSED`` are the declared ``invoke_model`` codes (``SPEC.md``).
``SILENT_FALLBACK_REFUSED``, ``PROVENANCE_INCOMPLETE``, and ``PROVENANCE_CONTRADICTED``
are reasoned refusals proposed by this adapter and queued for Bdo under O12; the
transition admits a reasoned refusal, but the exact code set is not ratified.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json


ADAPTER_DIR = Path(__file__).resolve().parent
ROOT = ADAPTER_DIR.parents[1]
ADAPTER_ID = "urn:soveraeign:adapter:ollama"
BINDING_SCHEMA = ROOT / "contracts" / "model-binding.schema.json"
INVENTORY = ADAPTER_DIR / "inventory.json"
BINDINGS_DIR = ADAPTER_DIR / "bindings"

PROVENANCE_FIELDS = ("provider_id", "model_id", "model_version", "runtime_id",
                     "runtime_version", "host_id")
INVOCATION_FIELDS = ("invocation_id", "binding_id", "operation_id", "actor_id",
                     "interface_contract_id", "required_authority", "requested_capability",
                     "input_projection_id", "input_digest", "omissions",
                     "data_boundary_applied", "executed", "usage", "cost",
                     "information_role", "outcome")
ADMITTED_ROLES = frozenset({"PROPOSAL", "RECORDING"})


class Refusal(Exception):
    """A named refusal with a reason code. Raising one never changes standing."""

    def __init__(self, reason_code: str, detail: str) -> None:
        super().__init__(detail)
        self.reason_code = reason_code
        self.detail = detail


def load_json(path: Path) -> Any:
    """Read one UTF-8 JSON document from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def check_binding(binding: dict, inventory: dict | None = None) -> dict:
    """Refuse a binding the recorded runtime does not support, or that misstates custody."""
    record = inventory if inventory is not None else load_json(INVENTORY)
    defects = _schema_defects(binding)
    if defects:
        raise Refusal("MODEL_INCOMPATIBLE", "; ".join(defects))
    if binding["adapter_id"] != ADAPTER_ID:
        raise Refusal("PROVENANCE_CONTRADICTED",
                      f"binding names adapter {binding['adapter_id']}, not {ADAPTER_ID}")

    source = record["source"]
    for field in ("runtime_id", "host_id"):
        if binding[field] != source[field]:
            raise Refusal("PROVENANCE_CONTRADICTED",
                          f"binding {field} {binding[field]!r} is not the recorded "
                          f"{source[field]!r}")
    if binding["runtime_version"] != source["runtime_version"]:
        raise Refusal("MODEL_UNAVAILABLE",
                      f"binding names runtime version {binding['runtime_version']}, "
                      f"inventory recorded {source['runtime_version']}")

    models = {model["model_id"]: model for model in record["models"]}
    model = models.get(binding["model_id"])
    if model is None:
        raise Refusal("MODEL_UNAVAILABLE", f"{binding['model_id']} is not in the inventory")
    if binding["model_version"] != model["model_version"]:
        raise Refusal("MODEL_UNAVAILABLE",
                      f"{binding['model_id']} is recorded at {model['model_version']}, "
                      f"binding names {binding['model_version']}")

    _check_custody(binding, model)
    absent = sorted(set(binding["capabilities"]) - set(model["capabilities"]))
    if absent:
        raise Refusal("MODEL_INCOMPATIBLE",
                      f"{binding['model_id']} does not hold {', '.join(absent)}")
    return {
        "outcome": "ACCEPTED",
        "binding_id": binding["binding_id"],
        "model_id": binding["model_id"],
        "provider_kind": binding["provider_kind"],
        "data_boundary": binding["data_boundary"],
        "authority_granted": False,
    }


def _check_custody(binding: dict, model: dict) -> None:
    """A model the runtime serves from another host is never LOCAL, whatever its tag says."""
    remote_host = model.get("remote_host")
    if remote_host and binding["provider_kind"] == "LOCAL":
        raise Refusal("DATA_BOUNDARY_REFUSED",
                      f"{model['model_id']} is served from {remote_host}; a LOCAL "
                      f"provider_kind misstates custody")
    if remote_host and binding["data_boundary"] == "LOCAL_ONLY":
        raise Refusal("DATA_BOUNDARY_REFUSED",
                      f"{model['model_id']} is served from {remote_host}; LOCAL_ONLY "
                      f"cannot hold across that crossing")
    if not remote_host and binding["provider_kind"] == "REMOTE":
        raise Refusal("PROVENANCE_CONTRADICTED",
                      f"{model['model_id']} is recorded with no remote host; REMOTE "
                      f"provider_kind is unsupported by the record")


def _schema_defects(binding: dict) -> list[str]:
    """Validate against the shared Model Binding contract, not against a local copy."""
    from sovkernel.jsonschema import validate

    return validate(binding, load_json(BINDING_SCHEMA))


def load_binding(binding_id: str) -> dict:
    """Find the declared binding by id. An invocation may not name a binding that is absent."""
    for path in sorted(BINDINGS_DIR.glob("*.json")):
        binding = load_json(path)
        if binding["binding_id"] == binding_id:
            return binding
    raise Refusal("MODEL_UNAVAILABLE", f"no declared binding {binding_id}")


def check_invocation(record: dict, inventory: dict | None = None) -> dict:
    """Refuse an invocation record that cannot account for what ran, or that ran elsewhere."""
    absent = [field for field in INVOCATION_FIELDS if field not in record]
    if absent:
        raise Refusal("PROVENANCE_INCOMPLETE", f"absent fields: {', '.join(absent)}")
    if record["information_role"] not in ADMITTED_ROLES:
        raise Refusal("PROVENANCE_CONTRADICTED",
                      f"model output entered as {record['information_role']}; admitted roles "
                      f"are {', '.join(sorted(ADMITTED_ROLES))}")

    binding = load_binding(record["binding_id"])
    check_binding(binding, inventory)
    executed = record["executed"]
    empty = [field for field in PROVENANCE_FIELDS
             if not str(executed.get(field) or "").strip()]
    if empty:
        raise Refusal("PROVENANCE_INCOMPLETE",
                      f"executed provenance absent: {', '.join(empty)}")

    _check_no_substitution(record, binding, executed)
    if record["data_boundary_applied"] == "LOCAL_ONLY" and executed.get("remote_host"):
        raise Refusal("DATA_BOUNDARY_REFUSED",
                      f"LOCAL_ONLY declared, input crossed to {executed['remote_host']}")
    if record["requested_capability"] not in binding["capabilities"]:
        raise Refusal("MODEL_INCOMPATIBLE",
                      f"{record['requested_capability']} is not bound by "
                      f"{binding['binding_id']}")
    for meter in ("usage", "cost"):
        if not isinstance(record[meter], dict) or not record[meter]:
            raise Refusal("PROVENANCE_INCOMPLETE", f"{meter} meter is empty")
    return {
        "outcome": "ACCEPTED",
        "invocation_id": record["invocation_id"],
        "binding_id": binding["binding_id"],
        "information_role": record["information_role"],
        "authority_granted": False,
    }


def _check_no_substitution(record: dict, binding: dict, executed: dict) -> None:
    """A replacement model is a new attributed invocation, never a quiet retry."""
    substituted = (executed["model_id"] != binding["model_id"]
                   or executed["model_version"] != binding["model_version"])
    if not substituted:
        return
    replacement = record.get("fallback_from_binding_id")
    if binding["fallback_policy"] != "EXPLICIT" or not replacement:
        raise Refusal("SILENT_FALLBACK_REFUSED",
                      f"{binding['binding_id']} binds {binding['model_id']}, "
                      f"{executed['model_id']} ran, and no replacement binding is named")
    raise Refusal("SILENT_FALLBACK_REFUSED",
                  f"an EXPLICIT fallback owes a new invocation bound to "
                  f"{executed['model_id']}, not a substitution inside the invocation of "
                  f"{binding['binding_id']}")


def check_parity(first: dict, second: dict, inventory: dict | None = None) -> dict:
    """Prove two materially different models ran one operation without moving anything else."""
    check_invocation(first, inventory)
    check_invocation(second, inventory)
    for field in ("interface_contract_id", "required_authority", "operation_id",
                  "input_projection_id", "input_digest", "requested_capability"):
        if first[field] != second[field]:
            raise Refusal("PROVENANCE_CONTRADICTED",
                          f"{field} differs across the two invocations: "
                          f"{first[field]!r} and {second[field]!r}")
    if first["executed"]["model_id"] == second["executed"]["model_id"]:
        raise Refusal("MODEL_INCOMPATIBLE",
                      "parity needs two materially different models; both invocations ran "
                      f"{first['executed']['model_id']}")
    if first["invocation_id"] == second["invocation_id"]:
        raise Refusal("PROVENANCE_CONTRADICTED", "both invocations carry one identity")
    return {
        "outcome": "ACCEPTED",
        "operation_id": first["operation_id"],
        "models": sorted([first["executed"]["model_id"], second["executed"]["model_id"]]),
        "required_authority": first["required_authority"],
        "authority_changed_with_model": False,
    }
