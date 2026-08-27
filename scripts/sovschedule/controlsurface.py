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

from sovschedule import authoring, changelog, console, control

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
    if outcome.outcome == changelog.PROPOSED:
        print("  the proposal is in .claude/schedules/change-log.ndjson. Bdo arms it,")
        print("  through the console page or with --as-owner at this terminal.")
    if outcome.moved:
        print(f"  {control.declaration_path(Path(args.root), args.name)} is changed and "
              "not committed.")
    return outcome.exit_code


def command_enable(args: argparse.Namespace) -> int:
    return _switch(args, changelog.ENABLE)


def command_disable(args: argparse.Namespace) -> int:
    return _switch(args, changelog.DISABLE)


def command_changes(args: argparse.Namespace) -> int:
    """Print the change log: every attempt, including the ones that were refused."""
    entries = changelog.read(Path(args.root))
    if getattr(args, "json", False):
        print(json.dumps([{
            "schedule": entry.schedule, "change": entry.change,
            "direction": entry.direction, "fields": list(entry.fields),
            "from_enabled": entry.from_enabled, "to_enabled": entry.to_enabled,
            "actor_id": entry.actor_id, "actor_kind": entry.actor_kind,
            "binding": entry.binding, "reason": entry.reason,
            "occurred_at": changelog.timestamp(entry.occurred_at),
            "outcome": entry.outcome, "refusal_code": entry.refusal_code,
        } for entry in entries], indent=2))
        return 0
    if not entries:
        print(f"{changelog.log_path(Path(args.root))} does not exist: no schedule "
              "has ever been created, edited or switched on this node.")
        return 0
    print(f"{'when':<21}{'schedule':<18}{'change':<8}{'move':<22}"
          f"{'outcome':<11}{'who':<8}reason")
    for entry in entries:
        move = (", ".join(entry.fields) if entry.fields
                else f"{entry.from_enabled} -> {entry.to_enabled}")
        outcome = entry.outcome + (f" ({entry.refusal_code})" if entry.refusal_code else "")
        print(f"{changelog.timestamp(entry.occurred_at):<21}{entry.schedule:<18}"
              f"{entry.change:<8}{move[:21]:<22}{outcome:<11}"
              f"{entry.actor_kind:<8}{entry.reason}")
    return 0


def _report(outcome) -> int:
    print(f"{outcome.outcome}: {outcome.detail}")
    return outcome.exit_code


def command_create(args: argparse.Namespace) -> int:
    """Write a new declaration, switched off. Arming it is a separate decision."""
    kind, _, target = str(args.target).partition(":")
    try:
        target_args = json.loads(args.args)
    except json.JSONDecodeError as error:
        print(f"REFUSED: --args is not JSON ({error})")
        return 1
    body = dict(authoring.blank(args.name))
    body.update({
        "description": args.description,
        "target": {"kind": kind, "name": target, "args": target_args},
        "cron": args.cron,
        "mode": args.mode,
        "effect_class": args.effect_class,
        "limits": {"max_budget_usd": args.budget, "timeout_seconds": args.timeout},
    })
    return _report(authoring.create(Path(args.root), args.name, body, _actor(args),
                                   args.reason))


def command_edit(args: argparse.Namespace) -> int:
    """Change named fields of an existing declaration. Each value is JSON."""
    changes = {}
    for pair in args.set:
        field, sep, raw = pair.partition("=")
        if not sep:
            print(f"REFUSED: --set expects FIELD=JSON, got {pair!r}")
            return 1
        try:
            changes[field] = json.loads(raw)
        except json.JSONDecodeError as error:
            print(f"REFUSED: the value for {field} is not JSON ({error}). "
                  f"Strings need quotes: --set {field}='\"...\"'")
            return 1
    if not changes:
        print("REFUSED: nothing to change; pass at least one --set FIELD=JSON")
        return 1
    return _report(authoring.update(Path(args.root), args.name, changes, _actor(args),
                                   args.reason))


def command_console(args: argparse.Namespace) -> int:
    """Serve the health page with working switches, on loopback only."""
    try:
        console.serve(Path(args.root), port=args.port, open_browser=not args.no_open)
    except (console.NonLoopbackBind, console.PortInUse) as refusal:
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

    log = sub.add_parser("changes", help="every recorded attempt to change a schedule")
    log.add_argument("--json", action="store_true")
    log.set_defaults(func=command_changes, root=ROOT)

    made = sub.add_parser("create", help="write a new schedule declaration, switched off")
    made.add_argument("name")
    made.add_argument("--target", required=True, help="workflow:<name> or skill:<name>")
    made.add_argument("--cron", required=True)
    made.add_argument("--description", default="")
    made.add_argument("--mode", default="observe", choices=("observe", "build"))
    made.add_argument("--effect-class", default="RESOURCE_CONSUMPTION",
                      choices=("RECORD_LOCAL", "RESOURCE_CONSUMPTION"))
    made.add_argument("--budget", type=float, default=3)
    made.add_argument("--timeout", type=int, default=1800)
    made.add_argument("--args", default="{}", help="JSON passed to the target")
    made.add_argument("--reason", required=True)
    made.add_argument("--as-owner", action="store_true")
    made.set_defaults(func=command_create, root=ROOT)

    change = sub.add_parser("edit", help="change one field of an existing declaration")
    change.add_argument("name")
    change.add_argument("--set", action="append", default=[], metavar="FIELD=JSON",
                        help="repeatable, e.g. --set cron='\"0 4 * * *\"'")
    change.add_argument("--reason", required=True)
    change.add_argument("--as-owner", action="store_true")
    change.set_defaults(func=command_edit, root=ROOT)

    live = sub.add_parser("console", help="serve the health page with working switches")
    live.add_argument("--port", type=int, default=0, help="0 picks a free port")
    live.add_argument("--no-open", action="store_true", help="do not open a browser")
    live.set_defaults(func=command_console, root=ROOT)
