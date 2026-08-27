"""The command-line binding for the switch operation, and the console launcher.

This is a binding and holds no authority of its own. It parses arguments, names who is
asking, and calls ``control.set_switch``; the grant is checked inside that function, so
a command line cannot arm anything a page could not, and neither can arm anything the
operation refuses.

Who is asking, by default, is a model. A session running this CLI is not the owner and
must not be able to arm a schedule by claiming to be him. ``--as-owner`` exists because
Bdo may work from a terminal rather than the console page, and it is a statement about
who is at the keyboard that gets written into the record verbatim.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json

from sovschedule import console, control, switchlog

ROOT = Path(__file__).resolve().parents[2]

#: The actor recorded when a model operator reaches this binding. It holds no seat, so
#: ENABLE comes back as a recorded proposal and the switch does not move.
MODEL_ACTOR = "urn:soveraeign:actor:cli-model-operator"


def _actor(args: argparse.Namespace) -> control.Actor:
    if getattr(args, "as_owner", False):
        return control.owner(control.BINDING_COMMAND)
    return control.model(MODEL_ACTOR, control.BINDING_COMMAND)


def _switch(args: argparse.Namespace, direction: str) -> int:
    outcome = control.set_switch(Path(args.root), args.name, direction,
                                 _actor(args), args.reason or "")
    print(f"{outcome.outcome}: {outcome.detail}")
    if outcome.outcome == switchlog.PROPOSED:
        print("  the proposal is in .claude/schedules/switch-log.ndjson. Bdo arms it,")
        print("  through the console page or with --as-owner at this terminal.")
    if outcome.moved:
        print(f"  {control.declaration_path(Path(args.root), args.name)} is changed and "
              "not committed.")
    return outcome.exit_code


def command_enable(args: argparse.Namespace) -> int:
    return _switch(args, switchlog.ENABLE)


def command_disable(args: argparse.Namespace) -> int:
    return _switch(args, switchlog.DISABLE)


def command_switches(args: argparse.Namespace) -> int:
    """Print the switch log: every attempt, including the ones that were refused."""
    entries = switchlog.read(Path(args.root))
    if getattr(args, "json", False):
        print(json.dumps([{
            "schedule": entry.schedule, "direction": entry.direction,
            "from_enabled": entry.from_enabled, "to_enabled": entry.to_enabled,
            "actor_id": entry.actor_id, "actor_kind": entry.actor_kind,
            "binding": entry.binding, "reason": entry.reason,
            "occurred_at": switchlog.timestamp(entry.occurred_at),
            "outcome": entry.outcome, "refusal_code": entry.refusal_code,
        } for entry in entries], indent=2))
        return 0
    if not entries:
        print(f"{switchlog.log_path(Path(args.root))} does not exist: no schedule's "
              "switch has ever been moved or asked about on this node.")
        return 0
    print(f"{'when':<21}{'schedule':<20}{'move':<26}{'outcome':<11}{'who':<8}reason")
    for entry in entries:
        move = f"{entry.from_enabled} -> {entry.to_enabled}"
        outcome = entry.outcome + (f" ({entry.refusal_code})" if entry.refusal_code else "")
        print(f"{switchlog.timestamp(entry.occurred_at):<21}{entry.schedule:<20}"
              f"{move:<26}{outcome:<11}{entry.actor_kind:<8}{entry.reason}")
    return 0


def command_console(args: argparse.Namespace) -> int:
    """Serve the health page with working switches, on loopback only."""
    try:
        console.serve(Path(args.root), port=args.port, open_browser=not args.no_open)
    except console.NonLoopbackBind as refusal:
        print(str(refusal))
        return 1
    return 0


def add_commands(sub: argparse._SubParsersAction) -> None:
    """Wire the four control verbs onto the existing schedule CLI."""
    for verb, func, help_text in (
        ("enable", command_enable, "arm one schedule (owner's; a model gets a proposal)"),
        ("disable", command_disable, "switch one schedule off"),
    ):
        parser = sub.add_parser(verb, help=help_text)
        parser.add_argument("name")
        parser.add_argument("--reason", required=True,
                            help="why - it is written into the switch log")
        parser.add_argument("--as-owner", action="store_true",
                            help="the owner is at this terminal; recorded as such")
        parser.set_defaults(func=func, root=ROOT)

    log = sub.add_parser("switches", help="every recorded attempt to move a switch")
    log.add_argument("--json", action="store_true")
    log.set_defaults(func=command_switches, root=ROOT)

    live = sub.add_parser("console", help="serve the health page with working switches")
    live.add_argument("--port", type=int, default=0, help="0 picks a free port")
    live.add_argument("--no-open", action="store_true", help="do not open a browser")
    live.set_defaults(func=command_console, root=ROOT)
