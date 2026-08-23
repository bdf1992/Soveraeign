"""Live model invocation against a local Ollama runtime.

This is the only module in the loop that touches a network socket, and it
reaches exactly one host: the operator's own machine. It refuses visibly rather
than substituting a model, because a silent fallback would make two different
runs look like one (`AGENTS.md`, Secrets and local boundaries).

`adapters/ollama/invoke.py` owns the general adapter path. This module is the
loop's narrow binding to it: read a declared binding, call the model it names,
and return a record carrying every provenance field
`contracts/tier-bindings.json` requires.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
BINDINGS = ROOT / "adapters" / "ollama" / "bindings"
ENDPOINT = "http://localhost:11434"


class Refusal(Exception):
    """A named, visible refusal. The loop never falls back to another model."""


def load_binding(binding_id: str) -> dict[str, Any]:
    """Read the declared binding whose `binding_id` matches, or refuse."""
    for path in sorted(BINDINGS.glob("*.json")):
        binding = json.loads(path.read_bytes().decode("utf-8"))
        if binding.get("binding_id") == binding_id:
            return binding
    raise Refusal(f"MODEL_INCOMPATIBLE: no declared binding for {binding_id}")


def project_input(prompt: str, omissions: list[str]) -> str:
    """The exact text sent to the model, with declared omissions withheld.

    `PRD.md` PROD-I-9 requires each run to record its input projection and what
    that projection left out. Withholding happens here so the recorded digest is
    the digest of what actually crossed.
    """
    lines = [line for line in prompt.splitlines()
             if not any(omitted in line for omitted in omissions)]
    return "\n".join(lines)


def _post(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    """POST JSON to the local runtime and return the decoded body."""
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def invoke(binding_id: str, prompt: str, *, purpose: str,
           timeout: float = 300.0) -> dict[str, Any]:
    """Call the model a binding names and return its provenance record.

    Refuses when the runtime is unreachable or the binding declares a boundary
    the call would cross. It never retries against a different model.
    """
    binding = load_binding(binding_id)
    if binding.get("data_boundary") != "LOCAL_ONLY":
        raise Refusal(f"DATA_BOUNDARY_REFUSED: {binding_id} declares "
                      f"{binding.get('data_boundary')}, the loop runs LOCAL_ONLY")
    projected = project_input(prompt, binding.get("omissions", []))
    started = time.monotonic()
    try:
        body = _post(f"{ENDPOINT}/api/generate",
                     {"model": binding["model_id"], "prompt": projected, "stream": False},
                     timeout)
    except (urllib.error.URLError, OSError) as error:
        raise Refusal(f"MODEL_UNAVAILABLE: {binding['model_id']} at {ENDPOINT}: {error}") from error
    wall = time.monotonic() - started

    return {
        "invocation_id": "urn:soveraeign:invocation:" + sha256(
            f"{binding_id}{purpose}{projected}".encode("utf-8")).hexdigest()[:16],
        "purpose": purpose,
        "binding_id": binding_id,
        "adapter_id": binding["adapter_id"],
        "provider_id": binding["provider_id"],
        "model_id": binding["model_id"],
        "model_version": binding["model_version"],
        "runtime_id": binding["runtime_id"],
        "host_id": binding["host_id"],
        "input_projection_id": binding["input_projection_id"],
        "input_digest": "sha256:" + sha256(projected.encode("utf-8")).hexdigest(),
        "data_boundary": binding["data_boundary"],
        "omissions": binding.get("omissions", []),
        "usage": {"input_tokens": body.get("prompt_eval_count", 0),
                  "output_tokens": body.get("eval_count", 0),
                  "wall_clock_seconds": round(wall, 3)},
        "cost": {"unit": binding["cost_meter"]["unit"],
                 "amount": 0, "basis": binding["cost_meter"]["basis"],
                 "wall_clock_seconds": round(wall, 3)},
        "output_text": body.get("response", ""),
        "output_digest": "sha256:" + sha256(
            body.get("response", "").encode("utf-8")).hexdigest(),
    }
