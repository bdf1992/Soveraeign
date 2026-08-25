"""Model Context Protocol server over stdio, standard library only.

MCP on stdio is JSON-RPC 2.0 with one message per line, which is small enough to
implement directly. Doing so keeps this binding inside the dependency policy in
`AGENTS.md` (Technical baseline: prefer the standard library) - no provider SDK
type reaches a service contract, and the gateway adds no runtime dependency.

The transport is local pipes. It opens no socket and reaches no network, so it
adds no external-world effect (`STATUS.yaml`, `no_external_effects_in_phase_i`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, TextIO
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).parent))

from gateway import EndpointRefused, Gateway  # noqa: E402


SERVER_NAME = "soveraeign"
SERVER_VERSION = "0.1.0"

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INTERNAL_ERROR = -32603


class Server:
    """One JSON-RPC session over a pair of text streams."""

    def __init__(self, gateway: Gateway, actor: str,
                 stdin: TextIO | None = None, stdout: TextIO | None = None) -> None:
        self.gateway = gateway
        self.actor = actor
        self.stdin = stdin if stdin is not None else sys.stdin
        self.stdout = stdout if stdout is not None else sys.stdout

    def serve(self) -> None:
        """Read one request per line until the stream closes."""
        for line in self.stdin:
            line = line.strip()
            if not line:
                continue
            response = self.handle_line(line)
            if response is not None:
                self.stdout.write(json.dumps(response) + "\n")
                self.stdout.flush()

    def handle_line(self, line: str) -> dict[str, Any] | None:
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            return _error(None, PARSE_ERROR, "invalid JSON")
        if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
            return _error(None, INVALID_REQUEST, "not a JSON-RPC 2.0 request")
        return self.handle(request)

    def handle(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Dispatch one request. A notification (no id) is acted on but not answered."""
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params") or {}
        if method == "initialize":
            result = {
                "protocolVersion": self.gateway.manifest["protocol_version"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            }
        elif method in ("notifications/initialized", "initialized"):
            return None
        elif method == "tools/list":
            result = {"tools": self.gateway.tools()}
        elif method == "tools/call":
            result = self.call_tool(params)
        elif method == "ping":
            result = {}
        else:
            if request_id is None:
                return None
            return _error(request_id, METHOD_NOT_FOUND, f"unknown method {method!r}")
        if request_id is None:
            return None
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def call_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run one tool call.

        A refusal is a tool result with `isError`, not a transport error: the
        caller asked a legal question and got a governed no, and the journal
        already holds the receipt for it.
        """
        name = params.get("name", "")
        arguments = params.get("arguments") or {}
        try:
            result = self.gateway.call(name, arguments, self.actor)
        except EndpointRefused as refusal:
            return _content(f"REFUSED {refusal.code}: {refusal}", is_error=True)
        except Exception as error:  # a service refusal is still a governed answer
            return _content(f"{type(error).__name__}: {error}", is_error=True)
        return _content(json.dumps(result, indent=2, sort_keys=True, default=str))


def _content(text: str, is_error: bool = False) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="soveraeign-mcp")
    parser.add_argument("--state-root", default=".soveraeign",
                        help="directory holding the asset and record stores")
    parser.add_argument("--actor", default="operator",
                        help="the participant identity every call is attributed to")
    args = parser.parse_args(argv)
    gateway = Gateway(Path(args.state_root))
    try:
        Server(gateway, args.actor).serve()
    finally:
        gateway.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
