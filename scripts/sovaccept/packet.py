"""Load, render, and act on one acceptance packet.

Rendering is the product here. The owner's whole job under decision 0028 is to
look at a finished result and answer; a packet that cannot be read in a minute
has failed even when every required field is present. So the rendering leads
with the claim, then the command the owner can run to see it, then the evidence,
and it prints the defeaters and residuals before the actions rather than after.

Recording an action writes what the owner did. It does not move standing: the
standing change lands in the owning governing document by an ordinary edit.
"""

from __future__ import annotations

from pathlib import Path
import json
import subprocess

from sovaccept import seats as registry

ACTIONS = ("ACCEPT", "REJECT", "STRIKE", "REDIRECT")
RULE = "-" * 78


def load(root: Path, packet_id: str) -> dict:
    """The packet with this id, read from ``acceptance/``."""
    path = root / "acceptance" / f"{packet_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"no packet {packet_id} at {path.relative_to(root).as_posix()}")
    return json.loads(path.read_bytes().decode("utf-8"))


def _actor(actor: dict | None) -> str:
    """One actor line, or the plain statement that nobody filled the seat."""
    if not actor:
        return "nobody yet"
    return f"{actor['actor_id']} ({actor['actor_kind']})"


def render(packet: dict) -> str:
    """The owner-facing presentation of one finished result."""
    subject = packet["subject"]
    lines = [
        RULE,
        f"  {packet['packet_id']}   {packet['claim']}",
        RULE,
        "",
        f"  {subject['artifact']}   {subject['from_standing']} -> {subject['to_standing']}",
        f"  built by {_actor(packet['built_by'])}    witnessed by "
        f"{_actor(packet.get('witnessed_by'))}",
        f"  {packet['presented_by_seat']} presents a {packet['claim_type']} claim "
        f"to {packet['accepted_by_seat']}, the seat one edge up",
        "",
        "  SEE IT YOURSELF",
        f"    $ {' '.join(packet['visible_result']['demo'])}",
        f"    shows   {packet['visible_result']['shows']}",
        f"    expect  {packet['visible_result']['expect']}",
        "",
        "  EVIDENCE",
    ]
    for item in packet["evidence"]:
        digest = f"  [{item['digest'][:12]}]" if item.get("digest") else ""
        lines.append(f"    {item['address']}{digest}")
        lines.append(f"        {item['says']}")
    lines += ["", "  WHY IT MATTERS", f"    {packet['why_it_matters']}", "",
              "  WHAT WOULD DEFEAT IT"]
    lines += [f"    - {row}" for row in packet["what_could_defeat_it"]]
    if packet.get("residuals"):
        lines += ["", "  KNOWN UNFINISHED"]
        lines += [f"    - {row}" for row in packet["residuals"]]
    lines += [
        "",
        "  YOUR CALL",
        f"    ACCEPT    {packet['on_accept']}",
        f"    REJECT    {packet['on_reject']}",
        "    STRIKE    the claim is withdrawn from the record entirely",
        "    REDIRECT  the result stands as evidence; the work turns elsewhere",
        "",
        f"    $ python scripts/sov_accept.py accept {packet['packet_id']} \\",
        f"          --seat {packet['accepted_by_seat']} --actor <the actor holding it>",
        RULE,
    ]
    return "\n".join(lines)


def run_demo(root: Path, packet: dict, tail: int = 12) -> tuple[int, str]:
    """Run the packet's demo command and return its exit code and last lines."""
    command = list(packet["visible_result"]["demo"])
    result = subprocess.run(command, cwd=root, check=False, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip().splitlines()
    return result.returncode, "\n".join(output[-tail:])


def refusals(root: Path, packet: dict, action: str, seat_id: str,
             actor_id: str) -> list[str]:
    """Why this seat and actor may not take this action on this packet.

    Ownership is one edge up (``decisions/0020``), so the question is never
    whether the actor is important enough. It is whether this exact seat owns
    the seat that presented, whether that seat settles this kind of claim, and
    whether the actor running the command is the one recorded in it.
    """
    problems = []
    if action not in ACTIONS:
        problems.append(f"UNKNOWN_ACTION: {action} is not one of {', '.join(ACTIONS)}")
    table = registry.load(root)
    problems += registry.edge_refusals(
        table, packet["presented_by_seat"], seat_id, packet["claim_type"])
    if seat_id != packet["accepted_by_seat"]:
        problems.append(
            f"ACCEPTANCE_BY_NON_OWNER: the packet is addressed to "
            f"{packet['accepted_by_seat']}, not {seat_id}")
    seated = registry.occupant_id(table, seat_id) if seat_id in registry.index(table) else None
    if seated is not None and actor_id != seated:
        problems.append(
            f"ACCEPTANCE_BY_NON_OWNER: {seat_id} is occupied by {seated}, not {actor_id}; "
            "claim the seat before acting from it")
    if actor_id == packet.get("built_by", {}).get("actor_id"):
        problems.append(
            "SELF_ACCEPTANCE_REFUSED: the actor accepting built the thing being accepted")
    return problems


def record(root: Path, packet: dict, action: str, seat_id: str, actor_id: str,
           when: str, note: str | None) -> dict:
    """Append one owner action to the local acceptance ledger and return the entry."""
    entry = {
        "recorded_at": when,
        "packet_id": packet["packet_id"],
        "claim": packet["claim"],
        "artifact": packet["subject"]["artifact"],
        "action": action,
        "presented_by_seat": packet["presented_by_seat"],
        "accepted_by_seat": seat_id,
        "claim_type": packet["claim_type"],
        "actor_id": actor_id,
        "note": note,
        "effect_class": "RECORD_LOCAL",
        "standing_change_lands_in": packet["subject"]["artifact"],
    }
    ledger = root / ".local" / "acceptance" / "ledger.ndjson"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry
