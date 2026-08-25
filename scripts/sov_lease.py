#!/usr/bin/env python3
"""Work leases: who is holding which concern, under what envelope, against what closure.

The live-session registry (`scripts/sov_session.py`) already answers "who is running".
This answers the three questions it cannot: what is that participant holding, what may it
spend doing it, and what would count as done. Same store, same session identity, same
liveness rule - a lease is not a second execution model, it is the session registry given
the nouns `contracts/work-lease.schema.json` declares.

A lease grants nothing. `take` records responsibility and an envelope; authority still
arrives by grant, and a lease with no grant reaches no further than the local record
(`AGENTS.md`, Authority).

Read commands (`status`) need no identity and change nothing. Write commands append an
event; nothing here ever edits a line.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovlease import commands  # noqa: E402
from sovlease import selfcheck  # noqa: E402
from sovsession import store  # noqa: E402


def _shared() -> argparse.ArgumentParser:
    """Options every subcommand accepts, on either side of the subcommand."""
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--name", default=argparse.SUPPRESS,
                        help="override this session's registry name")
    shared.add_argument("--json", action="store_true", dest="as_json",
                        default=argparse.SUPPRESS, help="emit machine-readable output")
    return shared


def _definition_options(parser: argparse.ArgumentParser) -> None:
    """What the invocation derives from, and who authored that definition."""
    parser.add_argument("--definition", required=True, help="agent, workflow or service id")
    parser.add_argument("--definition-kind", default="agent",
                        choices=["agent", "workflow", "skill", "service", "schedule", "human"])
    parser.add_argument("--provenance", default="SYSTEM_AUTHORED",
                        choices=["SYSTEM_AUTHORED", "USER_AUTHORED", "PERSONALIZED",
                                 "IMPORTED", "FORKED"])
    parser.add_argument("--definition-version", default="1")
    parser.add_argument("--derives-from", help="the upstream definition this diverged from")
    parser.add_argument("--definition-source", help="where the definition lives")


def _envelope_options(parser: argparse.ArgumentParser) -> None:
    """The grant, the budget, and the closure condition."""
    parser.add_argument("--grant", help="grant id; omitted means no grant and RECORD_LOCAL")
    parser.add_argument("--authority-type", choices=["VERIFICATION", "JUDGEMENT"])
    parser.add_argument("--capability", action="append", metavar="ID",
                        help="a capability the grant carries; repeatable")
    parser.add_argument("--effect-ceiling", default="RECORD_LOCAL",
                        choices=["RECORD_LOCAL", "RESOURCE_CONSUMPTION", "EXTERNAL_WORLD"])
    parser.add_argument("--budget", action="append", metavar="DIMENSION=LIMIT",
                        help="tokens=200000, wallclock_seconds=3600, turns=40; repeatable")
    parser.add_argument("--emit", action="append", metavar="COUNTER=LIMIT",
                        help="helper_leases=4, pull_requests=1, issues=0; repeatable")
    parser.add_argument("--minutes", type=int, default=commands.DEFAULT_MINUTES)
    parser.add_argument("--closure", required=True, help="what would count as done")
    parser.add_argument("--defeat", required=True, help="what would show it is not done")


def build_parser() -> argparse.ArgumentParser:
    """Assemble the command line."""
    shared = _shared()
    parser = argparse.ArgumentParser(description="Work leases over live sessions.",
                                     parents=[shared])
    parser.set_defaults(name=None, as_json=False)
    subparsers = parser.add_subparsers(
        dest="command", required=True,
        parser_class=lambda **kw: argparse.ArgumentParser(parents=[shared], **kw))

    take = subparsers.add_parser("take", help="hold a concern as this session")
    take.add_argument("reference", help="the ticket, operation, gate or seam being held")
    take.add_argument("--concern-kind", default="ticket",
                      choices=["ticket", "operation", "gate", "thread", "seam", "concern"])
    take.add_argument("--capability-served", metavar="ID",
                      help="the one canonical capability this work serves")
    take.add_argument("--lease-id", help="override the derived lease id")
    take.add_argument("--controller", default=None,
                      help="the principal that launched this one")
    take.add_argument("--principal", help="override the derived instance principal")
    _definition_options(take)
    _envelope_options(take)
    take.set_defaults(handler=commands.cmd_take)

    helper = subparsers.add_parser("helper", help="recruit a helper or witness under a lease")
    helper.add_argument("parent", help="the lease recruiting this one")
    helper.add_argument("reference", help="the part of the concern being handed over")
    helper.add_argument("--relation", default="HELPER", choices=["HELPER", "WITNESS"])
    helper.add_argument("--concern-kind", default="operation",
                        choices=["ticket", "operation", "gate", "thread", "seam", "concern"])
    helper.add_argument("--capability-served", metavar="ID")
    helper.add_argument("--lease-id")
    helper.add_argument("--principal", help="the helper's own instance principal")
    _definition_options(helper)
    _envelope_options(helper)
    helper.set_defaults(handler=commands.cmd_helper)

    draw = subparsers.add_parser("draw", help="record what a lease consumed or produced")
    draw.add_argument("lease")
    draw.add_argument("--consume", action="append", metavar="DIMENSION=AMOUNT")
    draw.add_argument("--produce", action="append", metavar="COUNTER=AMOUNT")
    draw.add_argument("--measured-by", default="hand", help="what took the measurement")
    draw.set_defaults(handler=commands.cmd_draw)

    close = subparsers.add_parser("close", help="declare closure with evidence")
    close.add_argument("lease")
    close.add_argument("--receipt", required=True)
    close.add_argument("--evidence", action="append", required=True, metavar="ADDRESS")
    close.add_argument("--standing", default="BUILT", choices=["BUILT", "WITNESSED"])
    close.add_argument("--witnessed-by", default=None)
    close.set_defaults(handler=commands.cmd_close)

    release = subparsers.add_parser("release", help="give the lease back, concern still open")
    release.add_argument("lease")
    release.set_defaults(handler=commands.cmd_release)

    fail = subparsers.add_parser("fail", help="stop short and say why")
    fail.add_argument("lease")
    fail.add_argument("--reason", required=True)
    fail.set_defaults(handler=commands.cmd_fail)

    status = subparsers.add_parser("status", help="what is held, by whom, inside what")
    status.add_argument("--lease", help="one lease instead of all of them")
    status.add_argument("--all", action="store_true", help="include closed leases")
    status.set_defaults(handler=commands.cmd_status)

    subparsers.add_parser(
        "selfcheck", help="prove the logic offline").set_defaults(
            handler=lambda args: selfcheck.run())
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch one command."""
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (commands.LeaseError, store.StoreError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
