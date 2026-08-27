"""Observe the MCP gateway from outside, over the wire it actually serves.

`bindings/mcp/tests/test_gateway.py` imports `Gateway` and calls it in process.
That establishes `BUILT`, and `AGENTS.md` holds that a build cannot witness
itself. This module takes the path a real MCP client takes instead: JSON-RPC 2.0
to `bindings/mcp/server.py` over stdio as a subprocess, nothing imported, and the
journal read back through the gateway's own `record_entries` tool rather than by
opening the store behind it.

Three steps are different and say so where they run: the startup validation
constructs `Gateway` directly, because `server.py` exposes no way to point at a
different manifest; the attribution check opens the asset store read-only, because
the divergence it looks for is between two records that no single tool returns
together; and one console grant is recorded before the server starts, because
`record_entries` began costing `read:journal` on 2026-08-25 and this binding exposes
no tool that issues a console grant. That provisioning runs in its own subprocess so
this module still imports nothing.

Running this establishes an independent observation. It proposes at most
`BUILT -> WITNESSED` and settles nothing.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
import json
import os
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "bindings" / "mcp" / "server.py"
MANIFEST_PATH = ROOT / "bindings" / "mcp" / "manifest.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
# A token-shaped label, to observe whether an argument reaches the journal whole.
# Assembled rather than written out: a literal of this shape in repository text is
# what scripts/lint.py exists to catch, and it is right to catch it.
SECRET_LABEL = "sk-" + "Z" * 28


class Observation:
    """What was asked over the wire, and what came back. Never a verdict."""

    def __init__(self) -> None:
        self.findings: list[tuple[bool, str, str]] = []

    def note(self, held: bool, claim: str, detail: str = "") -> None:
        self.findings.append((held, claim, detail))

    def report(self) -> int:
        width = max(len(claim) for _, claim, _ in self.findings)
        for held, claim, detail in self.findings:
            print(("PASS" if held else "FAIL") + "  " + claim.ljust(width) + "  " + detail)
        failed = [finding for finding in self.findings if not finding[0]]
        print("\n" + str(len(self.findings) - len(failed)) + "/" + str(len(self.findings))
              + " independent observations held")
        print("Standing note: an observation independent of the builder. It proposes at most "
              "BUILT -> WITNESSED and settles nothing.")
        return 1 if failed else 0


class Client:
    """One MCP session over a pipe pair, the way a model client would hold it."""

    def __init__(self, state_root: Path, actor: str) -> None:
        self.process = subprocess.Popen(
            [sys.executable, str(SERVER), "--state-root", str(state_root), "--actor", actor],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=str(ROOT), env=dict(os.environ), bufsize=1)
        self.next_id = 0

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send one JSON-RPC request and read the single line that answers it."""
        self.next_id += 1
        message: dict[str, Any] = {"jsonrpc": "2.0", "id": self.next_id, "method": method}
        if params is not None:
            message["params"] = params
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            raise SystemExit("server closed the stream: " + (self.process.stderr.read() or ""))
        return json.loads(line)

    def call(self, tool: str, **arguments: Any) -> dict[str, Any]:
        return self.request("tools/call", {"name": tool, "arguments": arguments})["result"]

    def text(self, tool: str, **arguments: Any) -> str:
        return self.call(tool, **arguments)["content"][0]["text"]

    def entries(self) -> list[dict[str, Any]]:
        return json.loads(self.text("record_entries"))

    def close(self) -> None:
        self.process.stdin.close()
        self.process.wait(timeout=60)


#: The node the gateway's console serves. A stale value here would provision the
#: wrong store and then report on a grant nobody holds.
NODE_ID = "node:local"
#: The name a caller types into `actor` that no record may end up carrying.
IMPOSTOR = "mallory"

PROVISION = """
import sys
sys.path[:0] = [{console_src!r}, {record_src!r}]
from soveraeign_console_service import ConsoleService
from soveraeign_record_service import RecordService
record = RecordService({journal!r})
ConsoleService(record, {console_dir!r}, {node!r}).grant(
    {actor!r}, "read:journal", {node!r}, {actor!r})
record.close()
"""


def _provision(state: Path, actor: str) -> str:
    """Record the one console grant `record_entries` costs, before the server starts.

    The journal read back here is the gateway's, at `<state>/record`, governed by a
    console whose own records sit at `<state>/console`; the console CLI cannot be
    aimed at that pair, so this writes the grant through the service in a subprocess
    and this module still imports nothing. Setup, not measurement: exactly
    `read:journal` over the node, so every gate below is bought or refused on its own.
    """
    script = PROVISION.format(
        console_src=str(ROOT / "services" / "console" / "src"),
        record_src=str(ROOT / "services" / "record" / "src"),
        journal=str(state / "record"), console_dir=str(state / "console"),
        node=NODE_ID, actor=actor)
    done = subprocess.run([sys.executable, "-c", script], cwd=str(ROOT),
                          capture_output=True, text=True)
    if done.returncode:
        raise SystemExit("could not provision the journal read: " + done.stderr.strip())
    return NODE_ID


def _refused(result: dict[str, Any], code: str) -> bool:
    return bool(result.get("isError")) and code in result["content"][0]["text"]


def _detail(result: dict[str, Any], limit: int = 58) -> str:
    return result["content"][0]["text"][:limit]


def _protocol(observed: Observation, client: Client) -> None:
    """The transport answers as JSON-RPC 2.0 and serves exactly what it declares."""
    initialized = client.request("initialize", {"protocolVersion": "2024-11-05"})
    observed.note(initialized["result"]["protocolVersion"] == MANIFEST["protocol_version"],
                  "initialize answers the declared protocol version",
                  str(initialized["result"]["protocolVersion"]))
    observed.note(client.request("ping")["result"] == {}, "ping answers")
    unknown = client.request("tools/frobnicate")
    observed.note(unknown.get("error", {}).get("code") == -32601,
                  "an unknown method is a JSON-RPC method-not-found",
                  str(unknown.get("error", {}).get("code")))
    served = {tool["name"] for tool in client.request("tools/list")["result"]["tools"]}
    declared = {entry["tool"] for entry in MANIFEST["endpoints"]}
    observed.note(served == declared, "the served tool list is exactly the manifest",
                  "served-only=" + str(sorted(served - declared))
                  + " manifest-only=" + str(sorted(declared - served)))
    observed.note(_refused(client.call("asset_delete_everything"), "UNKNOWN_OPERATION"),
                  "an unexposed tool is refused, not attempted")


def _gates(observed: Observation, client: Client, payload: Path) -> None:
    """A session, then a grant, then the call. Each refusal leaves a receipt."""
    early = client.call("asset_ingest", path=str(payload), label="early", actor="Bdo")
    observed.note(_refused(early, "SESSION_NOT_LIVE"),
                  "an act call before any session is refused", _detail(early))
    refusals = [entry for entry in client.entries()
                if entry["kind"] == "RECEIPT" and entry["payload"]["outcome"] == "REFUSED"]
    observed.note(bool(refusals), "the refusal is in the journal, not only in the answer",
                  str(len(refusals)) + " REFUSED receipts")

    depth = len(client.entries())
    client.text("asset_search", query="anything")
    observed.note(len(client.entries()) == depth, "a read-tier call appends nothing",
                  str(depth) + " entries before and after")

    session = json.loads(client.text("authority_open_session", participant="Bdo",
                                     model_identity="witness/1"))
    observed.note("session_id" in session, "a session opens", str(session["session_id"])[:24])
    ungranted = client.call("asset_ingest", path=str(payload), label="ungranted", actor="Bdo")
    observed.note(_refused(ungranted, "GRANT_NOT_HELD"),
                  "an act call with a session but no grant is refused", _detail(ungranted))

    client.text("authority_grant", issuer="Bdo", actor="Bdo",
                capability="operate:ingest", scope="assets/reports")
    narrow = client.call("asset_ingest", path=str(payload), label="narrow", actor="Bdo")
    observed.note(_refused(narrow, "GRANT_NOT_HELD"),
                  "a narrowly scoped grant admits no gateway-gated call",
                  _detail(narrow) if narrow.get("isError") else "ADMITTED under a narrow scope")

    client.text("authority_grant", issuer="Bdo", actor="Bdo",
                capability="operate:ingest", scope="*")
    committed = json.loads(client.text("asset_ingest", path=str(payload),
                                       label=SECRET_LABEL, actor="Bdo"))
    observed.note("receipt_id" in committed, "a granted act call commits and returns a receipt",
                  str(committed.get("receipt_id"))[:24])


def _journal(observed: Observation, client: Client) -> None:
    """What the journal keeps of an argument: its shape, never its bytes."""
    raw = json.dumps(client.entries())
    observed.note(SECRET_LABEL not in raw, "a secret-shaped argument is not journalled verbatim",
                  "searched " + str(len(raw)) + " bytes")
    shapes = {value for entry in client.entries() if entry["kind"] == "EVENT"
              for value in (entry["payload"].get("arguments") or {}).values()
              if isinstance(value, str)}
    observed.note(all(value.startswith("<") and value.endswith(">") for value in shapes),
                  "journalled arguments are shapes, not values",
                  ", ".join(sorted(shapes))[:64])


def _attribution(observed: Observation, client: Client, payload: Path, state: Path) -> None:
    """Which identity the gate reads, and which one the asset store records.

    The gateway checks `--actor`. `asset_ingest` also takes an `actor` argument,
    which reaches `AssetService.ingest` unchecked and lands on the asset store's
    own receipt. When the two differ, one act leaves two records naming different
    actors, and the caller chooses one of them.
    """
    diverged = client.call("asset_ingest", path=str(payload), label="attributed",
                           actor=IMPOSTOR)
    recorded = {entry.get("actor") for entry in client.entries()
                if entry["kind"] in ("EVENT", "RECEIPT")}
    stores = sorted(state.rglob("*.sqlite3")) + sorted(state.rglob("*.db"))
    asset_actors: list[str] = []
    for database in stores:
        connection = sqlite3.connect(database)
        connection.row_factory = sqlite3.Row
        named = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='receipts'").fetchone()
        if named:
            asset_actors = [row["actor"] for row in connection.execute(
                "SELECT actor FROM receipts")]
        connection.close()
    everywhere = {a for a in recorded if a} | set(asset_actors)
    # The property is that no record names the identity the caller typed, not that the
    # call was refused. Grading only the refusal made the better outcome - the binding
    # overwriting the argument with the gated identity - read as a failure.
    detail = ("refused: " + _detail(diverged) if diverged.get("isError")
              else "admitted as " + str(sorted(everywhere)))
    observed.note(IMPOSTOR not in everywhere,
                  "the actor argument cannot diverge from the gated identity", detail)


def _startup(observed: Observation, workspace: Path) -> None:
    """A declared endpoint with nothing behind it must refuse the start."""
    sys.path.insert(0, str(ROOT / "bindings" / "mcp"))
    from gateway import Gateway, UnbuiltEndpoint  # noqa: E402

    doctored = workspace / "doctored-manifest.json"
    broken = json.loads(json.dumps(MANIFEST))
    broken["endpoints"].append({"tool": "asset_teleport", "tier": "read", "service": "asset",
                                "operation": "teleport", "effect_class": "NONE",
                                "description": "declared, never built", "arguments": {}})
    doctored.write_text(json.dumps(broken), encoding="utf-8")
    unopened = workspace / "never-opened"
    try:
        Gateway(unopened, manifest_path=doctored).close()
        observed.note(False, "a declared endpoint with no implementation refuses the start",
                      "STARTED")
    except UnbuiltEndpoint as refusal:
        observed.note(True, "a declared endpoint with no implementation refuses the start",
                      str(refusal)[:58])
    observed.note(not unopened.exists(), "a refused start opens no store",
                  "created" if unopened.exists() else "no directory")


def observe() -> int:
    """Drive one full session over stdio and grade what came back."""
    observed = Observation()
    with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        workspace = Path(tmp)
        state = workspace / "state"
        payload = workspace / "payload.txt"
        payload.write_text("observed payload", encoding="utf-8")
        node = _provision(state, "Bdo")
        client = Client(state, actor="Bdo")
        try:
            observed.note(bool(node), "the journal read was bought before the walk",
                          "read:journal scoped to " + node)
            _protocol(observed, client)
            _gates(observed, client, payload)
            _journal(observed, client)
            _attribution(observed, client, payload, state)
        finally:
            client.close()
        _startup(observed, workspace)
    return observed.report()


if __name__ == "__main__":
    raise SystemExit(observe())
