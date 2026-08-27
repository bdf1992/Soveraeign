"""What each exposed operation actually does.

`gateway.py` owns the one path every call takes - resolve, bind the caller, check,
journal, execute, receipt. This owns the other half: the work at the end of it. The
two are separate responsibilities and the split keeps the dispatcher readable as a
single path rather than a path with seven bodies inlined in it.

A mixin rather than a module of functions, because `manifest_gate.audit_handlers`
reads these signatures and their annotations. Bound methods keep both; wrapping them
in `functools.partial` would drop `__annotations__` and blind the audit, which is the
one thing this file must not do to itself.

Every parameter here is either typed `Principal` and supplied by the dispatcher from
the authenticated caller, or declared in `manifest.json` as something the caller
sends. The audit refuses this binding at construction if that stops being true.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

# The root workspace is not packaged yet, so the built services are reached the way
# scripts/sov_witness.py reaches them (`AGENTS.md`, Python style: a test bootstrap
# may do this until the workspace is packaged).
sys.path.insert(0, str(ROOT / "services" / "console" / "src"))

from soveraeign_console_service import discover  # noqa: E402

from manifest_gate import Principal  # noqa: E402

#: The projection discovery answers from. One rebuildable source, checked by
#: `scripts/sov_capability.py check`, rather than a second list held here.
CAPABILITY_MAP = ROOT / "contracts" / "fixtures" / "capability-map.reference.json"


class Handlers:
    """The bodies behind the manifest's endpoints. Mixed into `Gateway`."""


    def _open_session(self, participant: Principal, model_identity: str,
                      ttl_seconds: float | None = None) -> dict[str, Any]:
        self.session_id = self.asset.open_session(participant, model_identity, ttl_seconds)
        return {"session_id": self.session_id, "participant": participant,
                "model_identity": model_identity}

    def _grant(self, issuer: Principal, actor: Principal, capability: str,
               scope: str = "*", ttl_seconds: float | None = None) -> dict[str, Any]:
        """`issuer` is the caller; `actor` is the grantee the caller names.

        Both are principals and only one is the caller, which is the distinction the
        manifest has to state: `issuer` is this endpoint's `caller_argument`, `actor`
        is declared under `subject_arguments`. The Asset Service attenuates what an
        issuer may hand on, so naming a grantee is not naming an authority.
        """
        kwargs: dict[str, Any] = {"scope": scope, "session_id": self.session_id}
        if ttl_seconds is not None:
            kwargs["ttl_seconds"] = ttl_seconds
        return {"grant_id": self.asset.grant(issuer, actor, capability, **kwargs)}

    def _ingest(self, path: str, label: str, actor: Principal) -> dict[str, str]:
        return self.asset.ingest(path, label, actor)

    def _search(self, query: str) -> list[str]:
        """The asset search projection.

        Wrapped rather than bound straight to `AssetService.search` so this binding
        owns the signature of everything it dispatches; `audit_handlers` reads these,
        and a signature owned by another service is one this binding cannot annotate.
        """
        return self.asset.search(query)

    def _entries(self) -> list[dict[str, Any]]:
        """The journal, for a caller holding `read:journal` over this node."""
        return self.record.entries()

    def _operations(self, operator_id: Principal) -> dict[str, Any]:
        """What this node declares, and what one operator holds, from the projection.

        The gateway supplies the map and says nothing about whether it is fresh: it
        reads the checked-in projection and has not rebuilt it, so `fresh` stays unset
        and the answer says nobody checked rather than implying somebody did.

        `operator_id` is not a tool argument. The manifest names it as this
        endpoint's `caller_argument`, so the dispatcher supplies the caller it was
        handed and a caller cannot ask what a different operator may do. The Console Service
        checks the `read:session` this operation declares as of 2026-08-25, so the
        name here decides whose grant is spent.
        """
        capability_map = json.loads(CAPABILITY_MAP.read_text(encoding="utf-8"))
        return discover(self.console, capability_map, operator_id)

    def _verify(self) -> dict[str, Any]:
        """Run the repository gate in a separate process and record what it returned."""
        completed = subprocess.run(
            [sys.executable, "scripts/verify.py"], cwd=ROOT, capture_output=True,
            text=True, timeout=120)
        tail = completed.stdout.strip().splitlines()[-3:]
        observation = {"exit_code": completed.returncode, "passed": completed.returncode == 0,
                       "tail": tail}
        self.record.append("OBSERVATION", "repository.verify", "gateway", observation)
        return observation
