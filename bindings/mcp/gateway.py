"""The dispatcher every exposed operation passes through.

One path, not one wrapper per operation: resolve the endpoint from
`manifest.json`, check the tier's preconditions, append the event, execute, and
append the receipt. A tool call already carries what an operation boundary needs
- a caller, a named operation, typed arguments, and a return - so the governed
crossing is built here once rather than restated at each endpoint.

The gateway is a Model Binding (`AGENTS.md`, Directory boundaries). It executes
within grants and never ratifies, settles, or witnesses. It holds no standing of
its own; `manifest.json` stands `PROPOSED`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("manifest.json")

# The root workspace is not packaged yet, so the two built services are reached
# the way scripts/sov_witness.py reaches them (`AGENTS.md`, Python style: a test
# bootstrap may do this until the workspace is packaged).
sys.path.insert(0, str(ROOT / "services" / "asset" / "src"))
sys.path.insert(0, str(ROOT / "services" / "console" / "src"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))

from soveraeign_asset_service import AssetService, AuthorityRefused  # noqa: E402
from soveraeign_console_service import ConsoleService, discover  # noqa: E402
from soveraeign_console_service import authority as console_authority  # noqa: E402
from soveraeign_console_service.refusals import (  # noqa: E402
    AuthorityRefused as ConsoleAuthorityRefused,
)
from soveraeign_record_service import RecordService  # noqa: E402

from manifest_gate import UnbuiltEndpoint, validate  # noqa: E402

#: The projection discovery answers from. One rebuildable source, checked by
#: `scripts/sov_capability.py check`, rather than a second list held here.
CAPABILITY_MAP = ROOT / "contracts" / "fixtures" / "capability-map.reference.json"
#: The node this gateway's console serves. A console that could run without naming its
#: node would emit records that do not say where they came from.
NODE_ID = "node:local"

class EndpointRefused(RuntimeError):
    """The gateway refused a call before any service saw it."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class Gateway:
    """Bind declared endpoints to built services and dispatch calls through one path.

    `state_root` holds both service stores, so a run started twice against the
    same root continues the same journal rather than starting a second one.
    """

    def __init__(self, state_root: str | Path, manifest_path: Path = MANIFEST) -> None:
        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.endpoints = {entry["tool"]: entry for entry in self.manifest["endpoints"]}
        self.withheld = {entry["tool"]: entry
                         for entry in self.manifest.get("withheld_endpoints", [])}
        validate(self.endpoints, self.withheld)
        self.state_root = Path(state_root)
        self.asset = AssetService(self.state_root / "asset")
        self.record = RecordService(self.state_root / "record")
        self.console = ConsoleService(self.record, self.state_root / "console", NODE_ID)
        self.session_id: str | None = None
        self._handlers = self._bind()

    def close(self) -> None:
        self.asset.close()
        self.record.close()

    # -- binding ----------------------------------------------------------

    def _bind(self) -> dict[str, Callable[..., Any]]:
        """Bind each validated endpoint name to the callable that serves it."""
        return {
            "authority_open_session": self._open_session,
            "authority_grant": self._grant,
            "asset_ingest": self._ingest,
            "asset_search": self.asset.search,
            "record_entries": self.record.entries,
            "console_operations": self._operations,
            "observe_verify": self._verify,
        }

    def tools(self) -> list[dict[str, Any]]:
        """The MCP tool descriptors, built from the manifest rather than hand-written."""
        described = []
        for entry in self.manifest["endpoints"]:
            properties = {}
            required = []
            for name, spec in entry.get("arguments", {}).items():
                properties[name] = {"type": spec["type"]}
                if spec.get("required"):
                    required.append(name)
            described.append({
                "name": entry["tool"],
                "description": f"[{entry['tier']}] {entry['description']}",
                "inputSchema": {"type": "object", "properties": properties,
                                "required": required, "additionalProperties": False},
            })
        return described

    # -- dispatch ---------------------------------------------------------

    def call(self, tool: str, arguments: dict[str, Any], actor: str) -> Any:
        """The one path every exposed operation takes.

        Read calls execute directly. Observe and act calls are journalled: an
        `EVENT` before the attempt and a `RECEIPT` after it, so a refusal and a
        crash are as visible in the journal as a success.
        """
        entry = self.endpoints.get(tool)
        if entry is None:
            raise EndpointRefused("UNKNOWN_OPERATION", f"{tool} is not an exposed endpoint")
        handler = self._handlers[tool]
        if entry.get("actor_is_operator"):
            # The principal the service checks a grant against is the caller this
            # gateway was handed, never a name the caller typed into the arguments.
            # Letting the argument win would let anyone spend anyone's grant, which
            # is what the endpoint costs since the Console Service began checking
            # the authority it declares (2026-08-25).
            arguments = {**arguments, "operator_id": actor}
        self._precheck(entry, actor)
        if entry["tier"] == "read":
            return handler(**arguments)
        journalled = self.record.append(
            "EVENT", entry["operation"], actor,
            {"tool": tool, "tier": entry["tier"], "effect_class": entry["effect_class"],
             "arguments": _redact(arguments), "session_id": self.session_id})
        try:
            result = handler(**arguments)
        except Exception as error:
            self.record.receipt("FAILED", entry["operation"], entry["operation"], actor,
                                {"entry_id": journalled["entry_id"],
                                 "error": type(error).__name__, "message": str(error)})
            raise
        self.record.receipt("COMMITTED", entry["operation"], entry["operation"], actor,
                            {"entry_id": journalled["entry_id"], "result": _summarize(result)})
        return result

    def _precheck(self, entry: dict[str, Any], actor: str) -> None:
        """A live session for everything that writes, then whichever gate the endpoint declares.

        Every tier passes through here. The read tier used to return before this ran,
        so `record_entries` - which declares `read:journal` and realizes
        `record.read-entry` - checked nothing and handed any caller the whole journal:
        thread titles, post ids, actor ids, content addresses, and every grant record
        the other endpoints' guards are read out of. That is not a policy this fixes
        by inventing one. `decisions/0052` moved the read to `FRONT/operator-desk` and
        said in the same breath that it still costs the `read:journal` grant; the code
        simply had not been asked for it.

        An endpoint whose authority is `service-enforced` gets no capability
        check here. Adding one would be a second rule with no bootstrap: the
        first grant of a store has nothing that could already cover it, which is
        exactly the hole the Authority layer's root rule exists to close.
        """
        if entry.get("requires_session", True):
            if self.session_id is None or not self.asset.authority.session_live(self.session_id):
                self._refuse(entry, actor, "SESSION_NOT_LIVE")
        node_capability = entry.get("node_authority")
        if node_capability is not None:
            self._node_precheck(entry, actor, node_capability)
            return
        if entry["tier"] != "act" or entry.get("authority") != "gateway":
            return
        if not self.asset.authority.authorized(actor, entry["capability"], "*"):
            self._refuse(entry, actor, "GRANT_NOT_HELD")

    def _node_precheck(self, entry: dict[str, Any], actor: str, capability: str) -> None:
        """Check a node capability against the node's own authority store.

        The console journal is where this node records who holds what, so a read of
        that journal is checked against it rather than against the Asset Service's
        separate store. The scope is the node: `record_entries` returns the journal
        entire, not one entry, so a grant narrower than the node would not cover what
        the endpoint actually serves.
        """
        try:
            console_authority.check(self.record.reconstruct(), NODE_ID, actor,
                                    capability, NODE_ID)
        except ConsoleAuthorityRefused:
            self._refuse(entry, actor, "GRANT_NOT_HELD")

    def _refuse(self, entry: dict[str, Any], actor: str, code: str) -> None:
        self.record.receipt("REFUSED", entry["operation"], entry["operation"], actor,
                            {"tool": entry["tool"], "reason": code})
        raise EndpointRefused(code, f"{actor} may not call {entry['tool']}: {code}")

    # -- handlers ---------------------------------------------------------

    def _open_session(self, participant: str, model_identity: str,
                      ttl_seconds: float | None = None) -> dict[str, Any]:
        self.session_id = self.asset.open_session(participant, model_identity, ttl_seconds)
        return {"session_id": self.session_id, "participant": participant,
                "model_identity": model_identity}

    def _grant(self, issuer: str, actor: str, capability: str, scope: str = "*",
               ttl_seconds: float | None = None) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"scope": scope, "session_id": self.session_id}
        if ttl_seconds is not None:
            kwargs["ttl_seconds"] = ttl_seconds
        return {"grant_id": self.asset.grant(issuer, actor, capability, **kwargs)}

    def _ingest(self, path: str, label: str, actor: str) -> dict[str, str]:
        return self.asset.ingest(path, label, actor)

    def _operations(self, operator_id: str) -> dict[str, Any]:  # actor_is_operator
        """What this node declares, and what one operator holds, from the projection.

        The gateway supplies the map and says nothing about whether it is fresh: it
        reads the checked-in projection and has not rebuilt it, so `fresh` stays unset
        and the answer says nobody checked rather than implying somebody did.

        `operator_id` is not a tool argument. The manifest marks this endpoint
        `actor_is_operator`, so the dispatcher supplies the caller it was handed and
        a caller cannot ask what a different operator may do. The Console Service
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


def _redact(arguments: dict[str, Any]) -> dict[str, Any]:
    """Journal argument shapes, not payloads: bounded excerpts, never whole values."""
    return {name: (value if isinstance(value, (int, float, bool)) else
                   f"<{type(value).__name__}:{len(str(value))}>")
            for name, value in arguments.items()}


def _summarize(result: Any) -> Any:
    """A bounded summary of a result, so the journal stays a record and not a copy."""
    if isinstance(result, (str, int, float, bool)) or result is None:
        return result
    if isinstance(result, dict):
        return {key: value for key, value in result.items() if isinstance(value, (str, int))}
    if isinstance(result, list):
        return {"count": len(result)}
    return {"type": type(result).__name__}


__all__ = ["AuthorityRefused", "EndpointRefused", "Gateway", "UnbuiltEndpoint"]
