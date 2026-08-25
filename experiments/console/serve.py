"""A local door onto the Console Service, for a human gesture and a model call alike.

There is one dispatch path. `GET /api/operations` returns the same discovery
answer the CLI's `operations` command gives, and `POST /api/call` invokes any of
them by name. The page builds its controls from that list rather than hardcoding
buttons, so an operation added to the service reaches the surface without the
page being edited, and a model driving this door uses exactly the calls a click
uses.

A refusal returns HTTP 409 with its stable `reason_code` and, when the service
wrote one, the receipt it wrote. This module routes; `door.py` owns what the
operations are and what the reads answer.

Local only, no authentication, no external effects. It binds 127.0.0.1 and
refuses anything else, because a console that quietly listened on a network
interface would be an external-world effect nobody admitted.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import views  # noqa: E402
from door import CALLS, NODE_ACTS, STORE, ConsoleRefusal, console  # noqa: E402
from views import READS  # noqa: E402

HOST, PORT = "127.0.0.1", 8787


# ---- http -------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    """One dispatcher. Reads are declared in READS, writes in CALLS."""

    server_version = "soveraeign-console-surface"

    def do_GET(self) -> None:  # noqa: N802 - http.server's interface
        path, _, query = self.path.partition("?")
        params = dict(pair.split("=", 1) for pair in query.split("&") if "=" in pair)
        if path in READS:
            try:
                return self._json(READS[path](params))
            except KeyError as error:
                return self._json({"error": "unknown", "detail": str(error)}, 404)
        if path in ("/", "/index.html"):
            return self._page(_latest_freeze())
        freeze = HERE / f"app.{path.lstrip('/')}.html"
        if freeze.exists():
            return self._page(freeze)
        return self._json({"error": "not_found", "freezes": _freezes()}, 404)

    def do_POST(self) -> None:  # noqa: N802 - http.server's interface
        if self.path != "/api/call":
            return self._json({"error": "not_found"}, 404)
        length = int(self.headers.get("Content-Length") or 0)
        try:
            request = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError as error:
            return self._json({"error": "bad_json", "detail": str(error)}, 400)
        name = request.get("operation")
        if name in NODE_ACTS:
            # Handled with no service open: these replace the store the service
            # would be holding.
            try:
                return self._json({"outcome": "COMMITTED", "operation": name,
                                   "record": NODE_ACTS[name](request.get("inputs") or {}),
                                   "receipt": None})
            except PermissionError as refused:
                return self._json({"outcome": "REFUSED", "operation": name,
                                   "reason_code": "CONFIRMATION_REQUIRED",
                                   "message": str(refused), "recorded": False,
                                   "receipt": None}, 409)
            except OSError as error:
                return self._json({"outcome": "REFUSED", "operation": name,
                                   "reason_code": "STORE_IN_USE", "message": str(error),
                                   "recorded": False, "receipt": None}, 409)
        if name not in CALLS:
            return self._json({"error": "unknown_operation", "operation": name,
                               "available": sorted([*CALLS, *NODE_ACTS])}, 404)
        with console() as svc:
            before = len(svc.record.reconstruct())
            try:
                record = CALLS[name][0](svc, request.get("inputs") or {})
            except ConsoleRefusal as refusal:
                # Most refusals are appended as a REFUSED receipt before the raise.
                # An authority refusal is not: `authority.check` raises directly, so
                # nothing is written. Returning the previous receipt would label an
                # unrelated entry as this refusal's proof, so the receipt is only
                # returned when this call actually grew the journal.
                return self._json({"outcome": "REFUSED", "operation": name,
                                   "reason_code": refusal.reason_code, "message": str(refusal),
                                   "recorded": len(svc.record.reconstruct()) > before,
                                   "receipt": views.last_receipt(svc)
                                   if len(svc.record.reconstruct()) > before else None}, 409)
            except KeyError as missing:
                return self._json({"error": "missing_input", "input": str(missing)}, 400)
            return self._json({"outcome": "COMMITTED", "operation": name, "record": record,
                               "receipt": views.last_receipt(svc)})

    def _json(self, payload: Any, code: int = 200) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _page(self, path: Path) -> None:
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        """One line per call, so what the surface did is visible without a debugger."""
        sys.stderr.write(f"  {args[0]}\n" if args else "")


def _freezes() -> list[str]:
    return sorted(p.stem.split(".", 1)[1] for p in HERE.glob("app.v*.html"))


def _latest_freeze() -> Path:
    names = _freezes()
    if not names:
        raise SystemExit("no app.v*.html in experiments/console")
    return HERE / f"app.{names[-1]}.html"


def main() -> None:
    """Serve. An absent store is a new node, not a failure to configure one.

    This used to refuse to start and name a command to run. A surface whose entry
    point requires a command typed elsewhere has moved its own first move onto
    the person; the empty node is a state the surface serves.
    """
    fresh = not (STORE / "journal").exists()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"console surface on http://{HOST}:{PORT}")
    print(f"freezes: {', '.join('/' + name for name in _freezes()) or 'none yet'}")
    print(f"store:   {STORE}{'  (new, empty)' if fresh else ''}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
