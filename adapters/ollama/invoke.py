"""Execute one ``invoke_model`` transition against the local Ollama runtime.

``adapter.py`` decides whether a declared binding and a *recorded* invocation are
admissible. This module produces that record by actually running the model: it applies
the binding's declared omissions to the input, sends the projected bytes to the runtime,
measures what the run consumed, resolves provenance from the runtime as it stands at
invocation time rather than from a stored inventory, and then submits its own output to
``check_invocation``. An executor that could emit a record its own checks would refuse
would be a second, quieter authority; this one cannot.

Effect class: ``RESOURCE_CONSUMPTION``. A local run spends wall clock, memory, and
electricity on owner-owned hardware. It accrues no monetary charge and it is not free.

Provenance comes from ``/api/tags`` read during the invocation, not from
``inventory.json``. A stored inventory records what was true when someone captured it;
the model that answers is the one loaded now, and the two can disagree.

Refusal reason codes are ``adapter.py``'s: ``MODEL_UNAVAILABLE``, ``MODEL_INCOMPATIBLE``,
and ``DATA_BOUNDARY_REFUSED`` are declared for ``invoke_model`` in ``SPEC.md``;
``SILENT_FALLBACK_REFUSED``, ``PROVENANCE_INCOMPLETE``, and ``PROVENANCE_CONTRADICTED``
are the adapter's proposed reasoned refusals.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
import re
import time

from adapter import Refusal, check_binding, check_invocation, load_binding

DEFAULT_ENDPOINT = "http://localhost:11434"
GENERATE_ROUTE = "/api/generate"
TAGS_ROUTE = "/api/tags"
VERSION_ROUTE = "/api/version"
DEFAULT_TIMEOUT = 300.0

#: Patterns for the omission classes the shipped bindings declare. A binding that
#: declares an omission this module cannot enforce is refused rather than sent.
OMISSION_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "lineage/evidence": (re.compile(r"lineage[/\\]evidence"),),
    "credentials": (
        re.compile(r"(?i)\b(api[_-]?key|secret|password|bearer|authorization)\b\s*[:=]"),
        re.compile(r"\b(sk-[A-Za-z0-9]{16,}|gh[pousr]_[A-Za-z0-9]{16,})\b"),
    ),
    "absolute host paths": (
        re.compile(r"[A-Za-z]:[/\\][^\s]+"),
        re.compile(r"(?<![\w.])/(?:home|Users|root|var|etc)/[^\s]+"),
    ),
}


class HttpTransport:
    """The one crossing this module makes: JSON over loopback to a local runtime."""

    def __init__(self, endpoint: str = DEFAULT_ENDPOINT, timeout: float = DEFAULT_TIMEOUT):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    def get(self, route: str) -> dict:
        """Read one JSON document from the runtime."""
        return self._read(Request(f"{self.endpoint}{route}", method="GET"))

    def post(self, route: str, payload: dict) -> dict:
        """Send one JSON document to the runtime and read its JSON answer."""
        request = Request(
            f"{self.endpoint}{route}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return self._read(request)

    def _read(self, request: Request) -> dict:
        try:
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310 loopback
                raw = response.read()
        except HTTPError as error:
            body = error.read().decode("utf-8", "replace")[:400]
            raise Refusal(
                "MODEL_UNAVAILABLE",
                f"{self.endpoint} answered HTTP {error.code}: {body}",
            ) from error
        except (URLError, OSError) as error:
            raise Refusal(
                "MODEL_UNAVAILABLE", f"{self.endpoint} did not answer: {error}"
            ) from error
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise Refusal(
                "PROVENANCE_INCOMPLETE",
                f"{self.endpoint} returned a body that is not JSON: {error}",
            ) from error


def project_input(prompt: str, omissions: list[str]) -> str:
    """Refuse an input carrying something the binding declared it would omit.

    Enforcement, not redaction. Silently stripping content would send bytes the caller
    did not author and address a digest over text the caller never saw.
    """
    unenforceable = [name for name in omissions if name not in OMISSION_PATTERNS]
    if unenforceable:
        raise Refusal(
            "DATA_BOUNDARY_REFUSED",
            f"binding declares omissions this adapter cannot enforce: "
            f"{', '.join(sorted(unenforceable))}",
        )
    for name in omissions:
        for pattern in OMISSION_PATTERNS[name]:
            found = pattern.search(prompt)
            if found:
                raise Refusal(
                    "DATA_BOUNDARY_REFUSED",
                    f"input carries {name!r}, which this binding omits "
                    f"(matched at offset {found.start()})",
                )
    return prompt


def digest(text: str) -> str:
    """Address the exact bytes that crossed, so a record can be checked against them."""
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _live_model(transport: Any, model_id: str) -> dict:
    """Resolve the model from the runtime as it stands now, not from a stored capture."""
    tags = transport.get(TAGS_ROUTE)
    for entry in tags.get("models", []):
        if entry.get("name") == model_id:
            return entry
    raise Refusal(
        "MODEL_UNAVAILABLE", f"{model_id} is not served by the runtime at invocation time"
    )


def _usage(body: dict, wall_clock_seconds: float) -> dict:
    """Read the meters off the response. An absent meter is a defect, not a zero.

    ``eval_count`` covers every token the model produced, and a thinking model spends
    an unpredictable share of them before it writes anything visible. The byte counts
    record where the spend went, so a record cannot report tokens consumed while
    implying they became output.
    """
    meters = {
        "input_tokens": body.get("prompt_eval_count"),
        "output_tokens": body.get("eval_count"),
    }
    absent = sorted(name for name, value in meters.items() if value is None)
    if absent:
        raise Refusal(
            "PROVENANCE_INCOMPLETE",
            f"runtime reported no {', '.join(absent)}; consumption is unaccounted",
        )
    return {
        **meters,
        "response_bytes": len((body.get("response") or "").encode("utf-8")),
        "thinking_bytes": len((body.get("thinking") or "").encode("utf-8")),
        "wall_clock_seconds": round(wall_clock_seconds, 3),
    }


def _settle(body: dict) -> tuple[str, str | None]:
    """Grade the run by what the runtime said it did, not by the fact that it answered.

    ``done_reason`` other than ``stop`` means the model was cut off. Such a run consumed
    resources and produced no terminal answer, which is ``UNRESOLVED`` in the ``SPEC.md``
    outcome vocabulary, never ``COMMITTED``.
    """
    reason = body.get("done_reason")
    if not body.get("done"):
        return "UNRESOLVED", "RUN_INCOMPLETE"
    if reason in (None, "stop"):
        return "COMMITTED", None
    return "UNRESOLVED", f"RUN_TRUNCATED_{str(reason).upper()}"


def _executed(binding: dict, body: dict, transport: Any) -> dict:
    """Provenance for what actually ran, taken from the runtime rather than the request."""
    ran = body.get("model")
    if not ran:
        raise Refusal("PROVENANCE_INCOMPLETE", "runtime named no model in its response")
    entry = _live_model(transport, ran)
    live_version = "sha256:" + entry["digest"] if entry.get("digest") else None
    if ran == binding["model_id"] and live_version != binding["model_version"]:
        raise Refusal(
            "PROVENANCE_CONTRADICTED",
            f"{ran} is loaded at {live_version}, the binding names "
            f"{binding['model_version']}",
        )
    return {
        "provider_id": binding["provider_id"],
        "model_id": ran,
        "model_version": live_version,
        "runtime_id": binding["runtime_id"],
        "runtime_version": transport.get(VERSION_ROUTE).get("version"),
        "host_id": binding["host_id"],
        "remote_host": entry.get("remote_host"),
    }


def invoke(
    binding_id: str,
    prompt: str,
    *,
    operation_id: str,
    actor_id: str,
    required_authority: str,
    invocation_id: str,
    capability: str = "completion",
    information_role: str = "PROPOSAL",
    transport: Any | None = None,
    inventory: dict | None = None,
    options: dict | None = None,
    monotonic: Callable[[], float] = time.monotonic,
) -> tuple[dict, str]:
    """Run one model invocation; return its record and the model's output text.

    The record is submitted to ``check_invocation`` before it is returned, so a record
    handed back here is one the adapter admits. Every failure path raises ``Refusal``
    with a reason code, and no path changes standing.
    """
    binding = load_binding(binding_id)
    check_binding(binding, inventory)
    if capability not in binding["capabilities"]:
        raise Refusal(
            "MODEL_INCOMPATIBLE", f"{capability} is not bound by {binding['binding_id']}"
        )

    projected = project_input(prompt, binding.get("omissions") or [])
    client = transport if transport is not None else HttpTransport()
    payload = {"model": binding["model_id"], "prompt": projected, "stream": False}
    if options:
        payload["options"] = options

    started = monotonic()
    body = client.post(GENERATE_ROUTE, payload)
    elapsed = monotonic() - started

    record = {
        "invocation_id": invocation_id,
        "binding_id": binding["binding_id"],
        "operation_id": operation_id,
        "actor_id": actor_id,
        "interface_contract_id": binding["interface_contract_id"],
        "required_authority": required_authority,
        "requested_capability": capability,
        "input_projection_id": binding["input_projection_id"],
        "input_digest": digest(projected),
        "omissions": list(binding.get("omissions") or []),
        "data_boundary_applied": binding["data_boundary"],
        "executed": _executed(binding, body, client),
        "usage": _usage(body, elapsed),
        "cost": {
            "unit": binding["cost_meter"]["unit"],
            "monetary_charge": binding["cost_meter"]["monetary_rate"],
            "basis": binding["cost_meter"]["basis"],
            "wall_clock_seconds": round(elapsed, 3),
        },
        "information_role": information_role,
        "output_digest": digest(body.get("response") or ""),
        "thinking_digest": digest(body.get("thinking") or ""),
        "done_reason": body.get("done_reason"),
    }
    record["outcome"], reason_code = _settle(body)
    if reason_code:
        record["reason_code"] = reason_code
    check_invocation(record, inventory)
    return record, body.get("response") or ""
