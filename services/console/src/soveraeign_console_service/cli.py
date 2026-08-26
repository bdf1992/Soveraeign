"""The Console Service machine interface.

`AI-NATIVE.md` gates on reachability: a fresh model instance must discover the
state, the available operations, the required inputs and the returned result
through a stable declared path. This CLI is that path. Every command reads JSON
arguments and writes one JSON object to stdout, including refusals, so a caller
never has to parse prose to learn what happened.

`operations` is the discovery command. It answers what may be done and what each
operation requires, and a human binding and a model binding get the same answer
from it because there is only one answer to give.

Exit codes: 0 committed, 2 refused, 3 unknown record, 1 usage error.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import argparse
import json
import sys

from soveraeign_console_service.continuity import (
    published_threads,
    read_thread,
    session_context,
)
from soveraeign_console_service.core import ConsoleService
from soveraeign_console_service.discovery import discover
from soveraeign_console_service.refusals import (
    CapabilityMapUnreadable,
    ConsoleRefusal,
    UnknownRecord,
)
from soveraeign_record_service import RecordService

DEFAULT_ROOT = Path(".local") / "console"
# The projection discovery answers from. Repository-relative rather than
# package-relative: the map is a shared contract, not console state.
DEFAULT_CAPABILITY_MAP = (Path("contracts") / "fixtures"
                         / "capability-map.reference.json")
# decisions/0039 takes the default that a node address is an opaque local identifier.
# This is that default made concrete for a console nobody has named yet; --node
# overrides it, and a crossing will require it to be named rather than defaulted.
DEFAULT_NODE = "node:local"


def _open(root: Path, node_id: str) -> ConsoleService:
    return ConsoleService(RecordService(root / "journal"), root, node_id)


def _emit(payload: dict[str, Any], code: int = 0) -> int:
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return code


def _capability_map(path: str) -> dict[str, Any]:
    """Read the capability projection, or refuse the way every other answer refuses.

    A missing file and an unparseable one used to leave a traceback on stderr and
    nothing on stdout, at exit 1, against this module's own promise that every answer
    including a refusal is one JSON object. `UNREADABLE` is the same code
    `discovery.readable` returns for a file that parses and is the wrong shape, because
    the caller's problem is the same one either way.
    """
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as unreachable:
        raise CapabilityMapUnreadable(
            f"the capability map at {path} cannot be read: "
            f"{type(unreachable).__name__}") from None
    except json.JSONDecodeError as malformed:
        raise CapabilityMapUnreadable(
            f"the capability map at {path} is not JSON: line {malformed.lineno}") from None


def _body(args: argparse.Namespace) -> bytes:
    """Read post content from --body or from stdin, so a caller can pipe a payload."""
    if args.body is not None:
        return args.body.encode("utf-8")
    return sys.stdin.buffer.read()


def _commands() -> dict[str, Callable[[ConsoleService, argparse.Namespace], dict[str, Any]]]:
    return {
        "operations": lambda c, a: discover(
            c, _capability_map(a.capability_map), a.operator, fresh=a.fresh),
        "grant": lambda c, a: c.grant(a.operator, a.capability, a.scope, a.granted_by),
        "revoke": lambda c, a: c.revoke(a.grant, a.revoked_by),
        "grants": lambda c, a: {"live_grants": c.grants(reader_id=a.reader,
                                                       operator_id=a.operator),
                                "authoritative": True},
        "open-channel": lambda c, a: c.open_channel(a.operator, a.name, a.domain),
        "open-thread": lambda c, a: c.open_thread(a.operator, a.channel, a.title,
                                                  a.pinned_address, a.pinned_digest),
        "archive-thread": lambda c, a: c.archive_thread(a.operator, a.thread),
        "open-session": lambda c, a: c.open_session(a.operator, a.actor_kind, a.binding),
        "close-session": lambda c, a: c.close_session(a.operator, a.session),
        "post": lambda c, a: c.post(a.operator, a.session, a.thread, _body(a),
                                    a.mention or (), a.claims, a.proposal_id),
        "read-thread": lambda c, a: read_thread(c, a.thread, a.binding,
                                                operator_id=a.operator),
        "list-publications": lambda c, a: published_threads(c, operator_id=a.operator),
        "publish-thread": lambda c, a: c.publish_thread(a.operator, a.thread),
        "withdraw-publication": lambda c, a: c.withdraw_publication(a.operator, a.publication),
        "session-context": lambda c, a: session_context(c, a.reader, a.operator),
    }


def build_parser() -> argparse.ArgumentParser:
    """Declare every command and its required inputs."""
    parser = argparse.ArgumentParser(prog="soveraeign-console", description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                        help="console store root (default .local/console)")
    parser.add_argument("--node", default=DEFAULT_NODE,
                        help=f"the node this console serves (default {DEFAULT_NODE})")
    sub = parser.add_subparsers(dest="command", required=True)

    operations = sub.add_parser(
        "operations", help="discover legal operations and their required inputs")
    operations.add_argument("--capability-map", dest="capability_map",
                            default=str(DEFAULT_CAPABILITY_MAP),
                            help=f"the capability projection to answer from "
                                 f"(default {DEFAULT_CAPABILITY_MAP})")
    operations.add_argument("--operator", required=True,
                            help="the operator asking; the answer costs a read:session "
                                 "grant scoped to it, so nobody asks anonymously")
    operations.add_argument("--stale", dest="fresh", action="store_false", default=None,
                            help="declare the projection stale, which refuses the answer "
                                 "rather than reporting from a map behind its sources")

    grant = sub.add_parser("grant", help="record a live grant for an operator")
    grant.add_argument("--operator", required=True)
    grant.add_argument("--capability", required=True)
    grant.add_argument("--scope", required=True)
    grant.add_argument("--granted-by", dest="granted_by", required=True,
                       help="the issuer whose grant:authority is spent. Required: it "
                            "defaulted to Bdo, and once this became the principal "
                            "checked rather than a label, the default let any caller "
                            "issue in the root seat's name without naming it")

    revoke = sub.add_parser("revoke", help="withdraw a grant by appending a revocation")
    revoke.add_argument("--grant", required=True)
    revoke.add_argument("--revoked-by", dest="revoked_by", required=True,
                        help="the revoker whose revoke:authority is spent; required "
                             "for the same reason as --granted-by")

    grants = sub.add_parser("grants", help="list the grants that are live right now")
    grants.add_argument("--reader", required=True,
                        help="the operator doing the reading; who holds what is node "
                             "state, so it costs a read:authority grant over the node")
    grants.add_argument("--operator", help="narrow the list to one operator")

    channel = sub.add_parser("open-channel", help="open a domain channel")
    channel.add_argument("--operator", required=True)
    channel.add_argument("--name", required=True)
    channel.add_argument("--domain", required=True)

    thread = sub.add_parser("open-thread", help="open a thread in a channel")
    thread.add_argument("--operator", required=True)
    thread.add_argument("--channel", required=True)
    thread.add_argument("--title", required=True)
    thread.add_argument("--pinned-address", dest="pinned_address")
    thread.add_argument("--pinned-digest", dest="pinned_digest")

    archive = sub.add_parser("archive-thread", help="archive a thread")
    archive.add_argument("--operator", required=True)
    archive.add_argument("--thread", required=True)

    publications = sub.add_parser(
        "list-publications", help="threads this node currently renders outwardly")
    publications.add_argument("--operator", required=True,
                              help="the operator asking; costs a read:thread grant "
                                   "scoped to the node")

    publish = sub.add_parser("publish-thread", help="mark a thread readable outside the node")
    publish.add_argument("--operator", required=True)
    publish.add_argument("--thread", required=True)

    withdraw = sub.add_parser("withdraw-publication",
                              help="stop rendering a thread outwardly; the mark stays recorded")
    withdraw.add_argument("--operator", required=True)
    withdraw.add_argument("--publication", required=True)

    session = sub.add_parser("open-session", help="open an operator session through a binding")
    session.add_argument("--operator", required=True)
    session.add_argument("--actor-kind", dest="actor_kind", required=True,
                         choices=("HUMAN", "MODEL"))
    session.add_argument("--binding", required=True)

    close = sub.add_parser("close-session", help="close a session and pin its read position")
    close.add_argument("--operator", required=True,
                       help="the operator closing it, which need not be whose session it is")
    close.add_argument("--session", required=True)

    post = sub.add_parser("post", help="post one attributed turn in a thread")
    post.add_argument("--operator", required=True,
                      help="the operator posting; it must own the session, and holding "
                           "a session id is not the same as being its operator")
    post.add_argument("--session", required=True)
    post.add_argument("--thread", required=True)
    post.add_argument("--body", help="post content; read from stdin when omitted")
    post.add_argument("--mention", action="append", help="operator id named in the post")
    post.add_argument("--claims", action="store_true",
                      help="the post makes a claim; a MODEL post then requires --proposal-id")
    post.add_argument("--proposal-id", dest="proposal_id")

    read = sub.add_parser("read-thread", help="read a thread through a binding")
    read.add_argument("--operator", required=True,
                      help="the operator reading; costs a read:thread grant scoped to "
                           "the thread")
    read.add_argument("--thread", required=True)
    read.add_argument("--binding")

    context = sub.add_parser("session-context",
                             help="what this operator needs to resume across a session boundary")
    context.add_argument("--reader", required=True,
                         help="the operator asking; costs a read:session grant scoped "
                              "to whose continuity is being read")
    context.add_argument("--operator", help="whose continuity to read (default: the reader)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    console = _open(args.root, args.node)
    try:
        return _emit(_commands()[args.command](console, args))
    except ConsoleRefusal as refusal:
        return _emit({"outcome": "REFUSED", "reason_code": refusal.reason_code,
                      "message": str(refusal)}, 2)
    except (UnknownRecord, KeyError) as missing:
        return _emit({"outcome": "REFUSED", "reason_code": UnknownRecord.reason_code,
                      "message": str(missing)}, 3)
    finally:
        console.record.close()


if __name__ == "__main__":
    raise SystemExit(main())
