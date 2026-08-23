#!/usr/bin/env python3
"""Record the local model runtime inventory that the adapter's checks read.

This is the adapter's one crossing: a read of a runtime listening on the loopback
interface, projected into ``inventory.json``. It runs only when a person asks it to.
Nothing in ``scripts/verify.py`` calls it, because a check that needs a live daemon
would report a passing result on a machine where the daemon merely happens to be
running, which says nothing about the binding it was supposed to check.

The projection keeps ``remote_host`` verbatim. A runtime can serve a model whose
weights execute on someone else's hardware under a local-looking name, and that fact
is the whole reason a ``LOCAL_ONLY`` binding needs checking against a record instead
of against a tag.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.request import urlopen
import json
import sys


ADAPTER = Path(__file__).resolve().parent
DEFAULT_ENDPOINT = "http://localhost:11434"
HOST_ID = "urn:soveraeign:host:local-node"


def read_endpoint(endpoint: str, route: str, timeout: float = 10.0) -> tuple[dict, str]:
    """Return one decoded JSON body and the sha256 of the exact bytes read."""
    with urlopen(f"{endpoint}{route}", timeout=timeout) as response:  # noqa: S310 loopback only
        raw = response.read()
    return json.loads(raw.decode("utf-8")), "sha256:" + sha256(raw).hexdigest()


def project_model(entry: dict) -> dict:
    """One inventory row. Absent optional fields are recorded as absent, not guessed."""
    details = entry.get("details") or {}
    return {
        "model_id": entry["name"],
        "model_version": "sha256:" + entry["digest"] if entry.get("digest") else None,
        "family": details.get("family"),
        "parameter_size": details.get("parameter_size"),
        "quantization_level": details.get("quantization_level"),
        "context_length": details.get("context_length"),
        "capabilities": sorted(entry.get("capabilities") or []),
        "remote_host": entry.get("remote_host"),
    }


def build(endpoint: str, now: datetime) -> dict:
    tags, tags_digest = read_endpoint(endpoint, "/api/tags")
    version, _ = read_endpoint(endpoint, "/api/version")
    models = sorted((project_model(entry) for entry in tags.get("models", [])),
                    key=lambda model: model["model_id"])
    return {
        "inventory_id": "urn:soveraeign:inventory:ollama:local-node",
        "information_role": "PROJECTION",
        "standing": "PROPOSED",
        "source": {
            "address": f"{endpoint}/api/tags",
            "capture_kind": "LOCAL_RUNTIME_READ",
            "effect_class": "RECORD_LOCAL",
            "runtime_id": "ollama",
            "runtime_version": version.get("version"),
            "host_id": HOST_ID,
            "captured_at": now.isoformat().replace("+00:00", "Z"),
            "response_digest": tags_digest,
        },
        "models": models,
    }


def main(argv: list[str]) -> int:
    endpoint = argv[1] if len(argv) > 1 else DEFAULT_ENDPOINT
    inventory = build(endpoint, datetime.now(timezone.utc))
    target = ADAPTER / "inventory.json"
    target.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"recorded {len(inventory['models'])} model(s) from {endpoint} into "
          f"{target.relative_to(ADAPTER.parents[1]).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
