"""A loopback HTTP console: the health read, with working switches on it.

A page opened from disk has no process behind it, so its buttons cannot change
anything. That is the whole reason this exists. It serves the same render the static
page uses, with a controls column, and posts back to the same operation the command
line calls - ``control.set_switch``, where the authority check lives.

What this is not. It is not a web server for anything but this box: it binds
``127.0.0.1`` and refuses any other address rather than trusting a flag. It mints a
token per run and prints it once, so a page you happen to be visiting cannot post into
your console; that is origin separation, not authentication, and the switch log records
the actor as a local operator rather than naming a person it never checked.

Effect class is ``RESOURCE_CONSUMPTION``: a listening socket on the owner's machine.
Nothing crosses a data boundary and no third party is reachable, so this is not the
``EXTERNAL_WORLD`` effect Phase I refuses.
"""

from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import json
import secrets
import threading
import webbrowser

from sovschedule import control, page, report, switchlog

LOOPBACK = "127.0.0.1"
TOKEN_BYTES = 24
MAX_BODY = 64 * 1024


class NonLoopbackBind(RuntimeError):
    """Asked to listen somewhere other than 127.0.0.1. Refused rather than warned about."""


class PortInUse(RuntimeError):
    """The requested port already belongs to something else."""


class Server(ThreadingHTTPServer):
    """A console server that will not share its port.

    ``allow_reuse_address`` defaults to true in the stdlib, and on Windows that flag
    does not mean what it means on Unix: it permits binding a port another process is
    actively listening on, with no error and no defined winner for incoming
    connections. This console bound a port that already held an unrelated application,
    printed a URL, and sent the operator to that application instead - a page with
    switches on it, pointed at somebody else's server. Refusing to share is the only
    safe setting for a surface that writes repository files.
    """

    allow_reuse_address = False


def mint_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


class Console:
    """The state one console run holds: where the repository is, and its token."""

    def __init__(self, root: Path, token: str, clock=None) -> None:
        self.root = root
        self.token = token
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def render(self) -> bytes:
        """The page as it stands right now, read from the working tree.

        The working tree, not HEAD: an operator looking at a switch is about to change
        that switch, and showing them the committed state would show them the thing
        they are not touching. The static page under docs/ reads HEAD and says so; this
        one says so too, on the page.
        """
        digest = report.assemble(self.root, self.clock(), source=report.WORKTREE)
        return page.render(digest, controls=self.token).encode("utf-8")

    def switch(self, payload: dict) -> tuple[int, dict]:
        """Perform one requested switch and answer with what the operation decided."""
        name = str(payload.get("schedule", ""))
        direction = str(payload.get("direction", ""))
        reason = str(payload.get("reason", ""))
        outcome = control.set_switch(
            self.root, name, direction, control.owner(control.BINDING_CONSOLE),
            reason, now=self.clock())
        return 200, {
            "outcome": outcome.outcome,
            "schedule": outcome.schedule,
            "direction": outcome.direction,
            "refusal_code": outcome.refusal_code,
            "detail": outcome.detail,
            "moved": outcome.moved,
        }


class Handler(BaseHTTPRequestHandler):
    """Three routes and a refusal. Everything unrecognised is a 404, including a probe."""

    console: Console

    protocol_version = "HTTP/1.1"
    server_version = "soveraeign-console"
    sys_version = ""

    def log_message(self, fmt: str, *args) -> None:
        """Quiet by default; the switch log is the record, not the access log."""

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # No embedding, no sniffing, no referrer leaving the box.
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def _refuse(self, code: int, message: str) -> None:
        self._send(code, json.dumps({"refusal": message}).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _token_ok(self, supplied: str | None) -> bool:
        return bool(supplied) and secrets.compare_digest(supplied, self.console.token)

    def do_GET(self) -> None:  # noqa: N802 - the stdlib names this
        parsed = urlparse(self.path)
        if parsed.path != "/":
            self._refuse(404, f"no route {parsed.path}")
            return
        supplied = parse_qs(parsed.query).get("t", [None])[0]
        if not self._token_ok(supplied):
            self._refuse(403, "BAD_TOKEN: open the URL this console printed when it started")
            return
        self._send(200, self.console.render(), "text/html; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802 - the stdlib names this
        parsed = urlparse(self.path)
        if parsed.path != "/switch":
            self._refuse(404, f"no route {parsed.path}")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._refuse(400, "unreadable Content-Length")
            return
        if length > MAX_BODY:
            self._refuse(413, "body too large")
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._refuse(400, "body is not JSON")
            return
        if not isinstance(payload, dict) or not self._token_ok(payload.get("token")):
            self._refuse(403, "BAD_TOKEN: this request did not come from the served page")
            return
        code, body = self.console.switch(payload)
        self._send(code, json.dumps(body).encode("utf-8"),
                   "application/json; charset=utf-8")


def build_server(root: Path, port: int = 0, host: str = LOOPBACK,
                 token: str | None = None, clock=None) -> tuple[ThreadingHTTPServer, str]:
    """Bind the console. Refuses any host but loopback; returns the server and its token.

    The refusal is here rather than in the caller because this is the only place that
    knows a socket is about to be bound. A flag that says loopback and a socket that
    binds elsewhere is exactly the gap worth closing in the module that opens it.
    """
    if host != LOOPBACK:
        raise NonLoopbackBind(
            f"NON_LOOPBACK_BIND: refused to listen on {host!r}. This console writes "
            "repository files and is for this machine only.")
    minted = token or mint_token()
    handler = type("BoundHandler", (Handler,),
                   {"console": Console(root, minted, clock=clock)})
    try:
        return Server((host, port), handler), minted
    except OSError as error:
        raise PortInUse(
            f"PORT_IN_USE: {host}:{port} is already listening, so this console did not "
            f"start ({error}). Pass a different --port, or omit it and the OS picks a "
            "free one.") from None


def url_for(server: ThreadingHTTPServer, token: str) -> str:
    return f"http://{LOOPBACK}:{server.server_address[1]}/?t={token}"


def _say(message: str) -> None:
    """Print and flush.

    Plain ``print`` block-buffers when stdout is a pipe, so a console started from a
    script or a task runner printed its URL only once the buffer filled - which is to
    say never, since it prints five lines and then blocks in serve_forever. The URL is
    the only way in, and a program that withholds its own entry point until it exits is
    no use to whoever started it.
    """
    print(message, flush=True)


def serve(root: Path, port: int = 0, open_browser: bool = True, out=_say) -> None:
    """Run the console until interrupted. The URL is printed once and carries the token."""
    server, token = build_server(root, port=port)
    address = url_for(server, token)
    out(f"console: {address}")
    out("  the switches on this page write .claude/schedules/ and commit nothing.")
    out("  arming a schedule is the owner's; a model reaching the same operation gets a")
    out("  recorded proposal and the switch does not move.")
    out("  stop with ctrl-c.")
    if open_browser:
        threading.Timer(0.3, webbrowser.open, args=(address,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        out("console: stopped.")
    finally:
        server.shutdown()
        server.server_close()


def switch_log_rows(root: Path, limit: int = 40) -> list[switchlog.Entry]:
    """The newest recorded attempts, for the console's own history panel."""
    return switchlog.read(root)[-limit:]
