#!/usr/bin/env python3
"""The owner gate, as a command.

Under ``decisions/0045-acceptance-not-approval.md`` the owner does not approve
work before it happens; the owner accepts or rejects a finished result. This
command is the whole surface of that gate.

    audit     fail when anything sits on the owner without a right to
    queue     what is waiting, and whether its packet is complete
    present   render one finished result so the call is obvious from the output
    accept | reject | strike | redirect   record the owner's answer

``audit`` runs inside ``scripts/verify.py``, so a run that parks work on Bdo
without naming an admissible reason fails the build. That is the point: before
this existed, an agent could stop on "ask Bdo" for free.

Every read and write is local. Recording an action writes a ledger line; it does
not move standing, which lands in the owning governing document by an edit.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sovaccept import packet as packets  # noqa: E402
from sovaccept import policy as acceptance  # noqa: E402


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def command_audit(args: argparse.Namespace) -> int:
    """Report every defect in the owner queue; fail the build on any of them."""
    defects = acceptance.audit(ROOT)
    register = acceptance.load_register(ROOT)
    if defects:
        print(f"FAIL: {len(defects)} defect(s) in the owner queue")
        for defect in defects:
            print(f"  {defect}")
        print("\nEvery defect above is a thing waiting on Bdo that has no admissible reason to "
              "wait. Rule it, present it, or record the reason.")
        return 1
    print(f"PASS: {len(register['rulings'])} ruling(s), "
          f"{len(register['owner_acceptance_queue'])} presented for acceptance, "
          f"{len(register['owner_holds'])} admissible hold(s), 0 open questions")
    return 0


def command_queue(args: argparse.Namespace) -> int:
    """What is waiting on the owner right now, and what is not."""
    register = acceptance.load_register(ROOT)
    defects = acceptance.audit(ROOT)
    print("== presented for acceptance ==")
    for item in register["owner_acceptance_queue"] or []:
        broken = [d for d in defects if str(item.get("id")) in d.detail]
        state = "INCOMPLETE" if broken else "ready"
        print(f"  {item.get('id'):6} [{state}]  {item.get('presented', '')}")
        print(f"         waits on {item.get('waits_on', 'an unnamed seat')}")
        print(f"         python scripts/sov_accept.py present {item.get('id')}")
    if not register["owner_acceptance_queue"]:
        print("  nothing. No finished result is waiting on Bdo.")
    print("\n== admissible holds ==")
    for hold in register["owner_holds"] or []:
        print(f"  {hold.get('id'):6} {hold.get('reason')} blocks {hold.get('blocks')}")
        print(f"         reachable meanwhile: {hold.get('reachable_alternative')}")
    if not register["owner_holds"]:
        print("  none")
    print(f"\n== standing defaults in force ==\n  {len(register['rulings'])} ruling(s); "
          "each names what would overturn it. python scripts/sov_accept.py rulings")
    return 0


def command_rulings(args: argparse.Namespace) -> int:
    """The defaults taken without asking, and what would overturn each."""
    for ruling in acceptance.load_register(ROOT)["rulings"]:
        print(f"  {ruling.get('id')}  {ruling.get('ruling')}")
        print(f"      overturned by: {ruling.get('counter')}")
    return 0


def command_present(args: argparse.Namespace) -> int:
    """Render one finished result for the owner, optionally running its demo."""
    packet = packets.load(ROOT, args.packet_id)
    print(packets.render(packet))
    if args.run:
        print("\n  RUNNING THE DEMO\n")
        code, output = packets.run_demo(ROOT, packet)
        for line in output.splitlines():
            print(f"    {line}")
        print(f"\n  demo exit {code}")
        return code
    return 0


def command_action(args: argparse.Namespace) -> int:
    """Record the owner's answer to one presented result."""
    packet = packets.load(ROOT, args.packet_id)
    action = args.action.upper()
    problems = packets.refusals(ROOT, packet, action, args.seat, args.actor)
    problems += [str(d) for d in acceptance.audit(ROOT) if packet["packet_id"] in d.detail]
    if problems:
        print(f"REFUSED: {action} {packet['packet_id']}")
        for problem in problems:
            print(f"  {problem}")
        return 1
    entry = packets.record(ROOT, packet, action, args.seat, args.actor,
                           args.at or _now(), args.note)
    print(json.dumps(entry, indent=2, sort_keys=True))
    print(f"\nRecorded. Now land the standing change in {packet['subject']['artifact']}:")
    print(f"  {packet['on_accept'] if action == 'ACCEPT' else packet['on_reject']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("audit", help="fail when anything waits on the owner without a reason")
    sub.add_parser("queue", help="what is waiting on the owner")
    sub.add_parser("rulings", help="defaults taken without asking, and what overturns them")

    present = sub.add_parser("present", help="render one finished result")
    present.add_argument("packet_id")
    present.add_argument("--run", action="store_true", help="run the packet's demo command")

    for action in ("accept", "reject", "strike", "redirect"):
        node = sub.add_parser(action, help=f"record {action.upper()}")
        node.add_argument("packet_id")
        node.add_argument("--seat", required=True,
                          help="the accepting seat, one edge up from the presenting seat")
        node.add_argument("--actor", required=True, help="the actor occupying that seat")
        node.add_argument("--note", default=None)
        node.add_argument("--at", default=None, help="ISO timestamp; defaults to now")
        node.set_defaults(action=action)

    args = parser.parse_args(argv)
    handlers = {"audit": command_audit, "queue": command_queue, "rulings": command_rulings,
                "present": command_present}
    return handlers.get(args.command, command_action)(args)


if __name__ == "__main__":
    raise SystemExit(main())
