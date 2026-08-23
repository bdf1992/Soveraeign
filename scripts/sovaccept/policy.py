"""Audit the owner queue against contracts/acceptance-policy.json.

The audit answers one question: is anything sitting on the owner that has no
right to sit there? A question with no admissible hold reason is a defect, not a
state, because under decision 0028 the owner gate is acceptance of a finished
result and wanting an opinion is not a reason to stop building.

Every defect is returned as a declared refusal code from the policy contract, so
a run can be read against the contract rather than against this module's prose.
"""

from __future__ import annotations

from pathlib import Path
import json
import re

from sovaccept import seats
from sovaccept import statusblock

TRANSITION = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")


class Defect(tuple):
    """One refusal: its declared code and the exact thing that earned it."""

    __slots__ = ()

    def __new__(cls, code: str, detail: str) -> "Defect":
        return super().__new__(cls, (code, detail))

    @property
    def code(self) -> str:
        return self[0]

    @property
    def detail(self) -> str:
        return self[1]

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


def load_policy(root: Path) -> dict:
    """The declared acceptance policy."""
    return json.loads((root / "contracts" / "acceptance-policy.json").read_bytes().decode("utf-8"))


def load_register(root: Path) -> dict[str, list[dict[str, object]]]:
    """The three owner-facing lists in STATUS.yaml, plus any undrained questions."""
    parsed = statusblock.parse((root / "STATUS.yaml").read_bytes().decode("utf-8"))
    return {
        name: statusblock.entries(parsed, name)
        for name in ("open_decisions", "owner_holds", "rulings", "owner_acceptance_queue")
    }


def _audit_holds(holds: list[dict[str, object]], policy: dict) -> list[Defect]:
    """A hold stands only for a declared reason, over one named transition."""
    reasons = policy["hold_reasons"]
    defects = []
    for hold in holds:
        name = hold.get("id") or "<unidentified hold>"
        if hold.get("reason") not in reasons:
            defects.append(Defect("HOLD_WITHOUT_ADMISSIBLE_REASON",
                                  f"{name} names reason {hold.get('reason')!r}, "
                                  f"absent from contracts/acceptance-policy.json hold_reasons"))
        blocks = hold.get("blocks")
        if not isinstance(blocks, str) or not TRANSITION.match(blocks):
            defects.append(Defect("HOLD_WITHOUT_NAMED_TRANSITION",
                                  f"{name} blocks {blocks!r}, which is not one "
                                  "subject.transition name"))
        if not hold.get("reachable_alternative"):
            defects.append(Defect("HOLD_WITHOUT_REACHABLE_ALTERNATIVE",
                                  f"{name} records nothing that stays reachable while it stands"))
    return defects


def _audit_rulings(rulings: list[dict[str, object]]) -> list[Defect]:
    """A default that cannot be overturned by evidence is a decree."""
    defects = []
    for ruling in rulings:
        name = ruling.get("id") or "<unidentified ruling>"
        if not ruling.get("ruling"):
            defects.append(Defect("UNDRAINED_QUESTION", f"{name} records no ruling"))
        if not ruling.get("counter"):
            defects.append(Defect("RULING_WITHOUT_COUNTER",
                                  f"{name} names no condition that would overturn it"))
    return defects


def _audit_queue(queue: list[dict[str, object]], root: Path, policy: dict,
                 schema: dict) -> list[Defect]:
    """Every presented item resolves to a complete, schema-valid packet."""
    from sovkernel.jsonschema import validate

    defects = []
    for item in queue:
        name = item.get("id") or "<unidentified acceptance item>"
        relative = item.get("packet")
        path = root / str(relative) if relative else None
        if not relative or path is None or not path.is_file():
            defects.append(Defect("PACKET_INCOMPLETE",
                                  f"{name} names packet {relative!r}, which is not a file"))
            continue
        packet = json.loads(path.read_bytes().decode("utf-8"))
        for error in validate(packet, schema):
            defects.append(Defect("PACKET_INCOMPLETE", f"{name} {error}"))
        for section in policy["packet_required_sections"]:
            if not packet.get(section):
                defects.append(Defect("PACKET_INCOMPLETE",
                                      f"{name} packet has no {section}"))
        if not packet.get("what_could_defeat_it"):
            defects.append(Defect("PACKET_WITHOUT_DEFEATER",
                                  f"{name} packet names no condition that would defeat it"))
        if packet.get("packet_id") != item.get("id"):
            defects.append(Defect("PACKET_INCOMPLETE",
                                  f"{name} packet declares id {packet.get('packet_id')!r}"))
        defects += _audit_edge(name, packet, root)
        if item.get("waits_on") != packet.get("accepted_by_seat"):
            defects.append(Defect("ACCEPTANCE_BY_NON_OWNER",
                                  f"{name} waits on {item.get('waits_on')!r} in STATUS.yaml but "
                                  f"its packet is addressed to "
                                  f"{packet.get('accepted_by_seat')!r}"))
    return defects


def _audit_edge(name: str, packet: dict, root: Path) -> list[Defect]:
    """The packet routes one edge up, to a seat that settles this kind of claim."""
    presenting = packet.get("presented_by_seat")
    accepting = packet.get("accepted_by_seat")
    claim_type = packet.get("claim_type")
    if not (presenting and accepting and claim_type):
        return [Defect("PACKET_INCOMPLETE", f"{name} packet names no acceptance edge")]
    table = seats.load(root)
    return [Defect(problem.split(":", 1)[0], f"{name} {problem.split(': ', 1)[-1]}")
            for problem in seats.edge_refusals(table, presenting, accepting, claim_type)]


def _audit_orphans(queue: list[dict[str, object]], root: Path) -> list[Defect]:
    """A packet nobody presented is a result the owner will never be shown."""
    presented = {str(item.get("packet")) for item in queue}
    defects = []
    for path in sorted((root / "acceptance").glob("A*.json")):
        relative = path.relative_to(root).as_posix()
        if relative not in presented:
            defects.append(Defect("UNDRAINED_QUESTION",
                                  f"{relative} exists but STATUS.yaml presents no such item"))
    return defects


def audit(root: Path) -> list[Defect]:
    """Every defect in the owner queue, as declared refusal codes."""
    policy = load_policy(root)
    register = load_register(root)
    schema = json.loads(
        (root / "contracts" / "acceptance-packet.schema.json").read_bytes().decode("utf-8"))
    defects = [
        Defect("UNDRAINED_QUESTION",
               f"{entry.get('id')} is an open decision: rule it, present it, or record an "
               "admissible hold")
        for entry in register["open_decisions"]
    ]
    defects += _audit_holds(register["owner_holds"], policy)
    defects += _audit_rulings(register["rulings"])
    defects += _audit_queue(register["owner_acceptance_queue"], root, policy, schema)
    defects += _audit_orphans(register["owner_acceptance_queue"], root)
    return defects
