#!/usr/bin/env python3
"""Minimal Phase-I node listener.

This process proves only the runtime/listener/health seam. It does not activate a
Gateway operation. All non-health requests are refused until a separate governed
operation supplies application behavior.
"""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import sys
from typing import Any


HEALTH_PATHS = {"/health/startup", "/health/ready", "/health/live"}


class BoundedHTTPServer(HTTPServer):
    request_queue_size = 1


class NodeHandler(BaseHTTPRequestHandler):
    server_version = "SoveraeignPhaseI/1"

    def _write_json(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _route(self) -> None:
        if self.path in HEALTH_PATHS:
            self._write_json(200, {"outcome": "PASS", "surface": self.path})
            return
        self._write_json(503, {
            "outcome": "REFUSED",
            "reason": "GATEWAY_OPERATION_NOT_ACTIVATED",
        })

    def do_GET(self) -> None:  # noqa: N802 - stdlib callback name
        self._route()

    def do_HEAD(self) -> None:  # noqa: N802 - stdlib callback name
        self._route()

    def do_POST(self) -> None:  # noqa: N802 - stdlib callback name
        self._route()

    def do_PUT(self) -> None:  # noqa: N802 - stdlib callback name
        self._route()

    def do_PATCH(self) -> None:  # noqa: N802 - stdlib callback name
        self._route()

    def do_DELETE(self) -> None:  # noqa: N802 - stdlib callback name
        self._route()

    def log_message(self, format: str, *args: object) -> None:
        print(format % args, file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default=os.environ.get("SOVERAEIGN_GATEWAY_BIND", "0.0.0.0"))
    parser.add_argument("--port", type=int,
                        default=int(os.environ.get("SOVERAEIGN_GATEWAY_PORT", "8080")))
    args = parser.parse_args(argv)
    if args.port < 1 or args.port > 65535:
        print(json.dumps({"outcome": "REFUSED", "reason": "PORT_INVALID"}, sort_keys=True))
        return 2
    server = BoundedHTTPServer((args.bind, args.port), NodeHandler)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
