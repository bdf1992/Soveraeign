"""Press the seat etiquette checker with defects no fixture prepared for it.

`scripts/tests/test_seat_etiquette.py` runs the fourteen defeating fixtures in
`contracts/fixtures/seat-message.fixtures.json`. That proves the checker catches
the cases it was shown. It cannot answer the different question this module asks:
does the checker read `contracts/seat-etiquette.json`, or does it recognise the
fixtures?

So each check here starts from a positive fixture the checker admits, breaks it in
a way the table forbids but no fixture covers, and requires a defect. The carriage
checks go further and inject a dissent and a stall the positive corpus never
carries, because a duty declared over four kinds is only observed over two.

Running this establishes an independent observation about the checker. It settles
nothing about the etiquette itself, which is a proposal
(`decisions/0035-seat-message-etiquette.md`).
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Callable
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.seat_etiquette import conversation_defects  # noqa: E402

CONTRACTS = ROOT / "contracts"
FIXTURES = CONTRACTS / "fixtures"
ETIQUETTE = json.loads((CONTRACTS / "seat-etiquette.json").read_text(encoding="utf-8"))
TOPOLOGY = json.loads((FIXTURES / "seat-topology.reference.json").read_text(encoding="utf-8"))
ENTRIES = json.loads((FIXTURES / "seat-message.fixtures.json").read_text(encoding="utf-8"))
BY_ID = {entry["id"]: entry for entry in ENTRIES}

# A proven BLOCKED claim carries all seven fields or it is a gate, not a block.
STALL = {"item_id": "S1", "raised_by": "sov-worker@1", "held_ticket": "T-1",
         "transition": "BUILT -> WITNESSED", "missing_precondition": "no independent observer",
         "governing_rule": "AGENTS.md, no self-witnessing", "required_authority": "root",
         "unblock_condition": "a second actor observes", "reachable_alternative": "NONE"}
DISSENT = {"item_id": "D1", "raised_by": "sov-witness@1", "claim": "the lease expires",
           "dissent": "it does not; the fixture never sets an expiry"}


class Observation:
    """What was pressed, and whether the checker refused it."""

    def __init__(self) -> None:
        self.findings: list[tuple[bool, str, str]] = []

    def note(self, held: bool, claim: str, detail: str = "") -> None:
        self.findings.append((held, claim, detail))

    def report(self) -> int:
        width = max(len(claim) for _, claim, _ in self.findings)
        for held, claim, detail in self.findings:
            print(("PASS" if held else "FAIL") + "  " + claim.ljust(width) + "  " + detail)
        failed = [f for f in self.findings if not f[0]]
        print("\n" + str(len(self.findings) - len(failed)) + "/" + str(len(self.findings))
              + " independent observations held")
        print("Standing note: an observation about the checker, independent of its own "
              "fixtures. The etiquette it enforces remains a proposal.")
        return 1 if failed else 0


def conversation(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """The statements made before this entry's record, then the record itself."""
    return deepcopy(list(entry.get("context", [])) + [entry["record"]])


def defects(statements: list[dict[str, Any]]) -> list[str]:
    return list(conversation_defects(statements, TOPOLOGY, ETIQUETTE))


def seat(message: dict[str, Any], seat_id: str, seat_type: str) -> None:
    message["speaker"]["seat_id"] = seat_id
    message["speaker"]["seat_type"] = seat_type


def press(observed: Observation, entry_id: str, claim: str,
          break_it: Callable[[dict[str, Any]], None]) -> None:
    """Break the final statement of an admitted fixture and require a defect."""
    entry = BY_ID.get(entry_id)
    if entry is None:
        observed.note(False, claim, "fixture " + entry_id + " is absent")
        return
    statements = conversation(entry)
    standing = defects(statements)
    if standing:
        observed.note(False, claim, "baseline already defective: " + "; ".join(standing)[:60])
        return
    break_it(statements[-1])
    found = defects(statements)
    observed.note(bool(found), claim, "; ".join(found)[:96] if found else "NOT CAUGHT")


def press_carriage(observed: Observation, kind: str, item: dict[str, Any]) -> None:
    """Carry an item the positive corpus never carries, then drop it at each hop."""
    entry = BY_ID["SEATMSG-POS-CONTROL-AGGREGATE"]
    carried = conversation(entry)
    for index in (0, 2, 3):
        carried[index]["carries"][kind] = [item]
    observed.note(not defects(carried), "a " + kind[:-1] + " carried to the root is admitted",
                  "; ".join(defects(carried))[:80])
    for index, hop in ((3, "control"), (2, "orchestration")):
        dropped = deepcopy(carried)
        dropped[index]["carries"][kind] = []
        found = defects(dropped)
        observed.note(bool(found), "the " + hop + " seat may not drop a " + kind[:-1],
                      "; ".join(found)[:80] if found else "NOT CAUGHT")


def observe() -> int:
    """Press every rule the table states and the fixtures do not reach."""
    observed = Observation()
    positives = [entry for entry in ENTRIES if entry["polarity"] == "positive"]
    admitted = [entry for entry in positives if not defects(conversation(entry))]
    observed.note(len(admitted) == len(positives), "every positive fixture is admitted as written",
                  str(len(admitted)) + "/" + str(len(positives)))

    # An act absent from a seat's `may` list.
    press(observed, "SEATMSG-POS-WORK-ATTEST", "an orchestration seat may not ATTEST",
          lambda m: seat(m, "seat:orchestrator-1", "orchestration"))
    press(observed, "SEATMSG-POS-ROOT-HOLD", "the root seat may not ASK",
          lambda m: m.__setitem__("act", "ASK"))
    press(observed, "SEATMSG-POS-WORK-REPORT", "a work seat may not DISPATCH",
          lambda m: m.__setitem__("act", "DISPATCH"))

    # The relation each act requires.
    press(observed, "SEATMSG-POS-CONTROL-AGGREGATE", "an AGGREGATE claiming PERFORMED is refused",
          lambda m: m["speaker"].__setitem__("relation_to_subject", "PERFORMED"))
    press(observed, "SEATMSG-POS-ROOT-HOLD", "a HOLD claiming PERFORMED is refused",
          lambda m: m["speaker"].__setitem__("relation_to_subject", "PERFORMED"))

    # The standing ceiling each act carries.
    press(observed, "SEATMSG-POS-WORK-ATTEST", "an ATTEST may not start from OPEN",
          lambda m: m.__setitem__("standing_proposed", {"from": "OPEN", "to": "WITNESSED"}))
    press(observed, "SEATMSG-POS-WORK-REPORT", "a REPORT may not reach WITNESSED",
          lambda m: m.__setitem__("standing_proposed", {"from": "BUILT", "to": "WITNESSED"}))

    # The generative rule: a seat absent from the topology has no admissible acts.
    press(observed, "SEATMSG-POS-WORK-REPORT", "an unregistered seat may say nothing",
          lambda m: seat(m, "seat:ghost-1", "advisory"))
    press(observed, "SEATMSG-POS-WORK-REPORT", "a statement to an unregistered seat is refused",
          lambda m: m.__setitem__("to_seat", "seat:worker-2"))

    # The carriage duty over the two kinds no positive fixture exercises.
    press_carriage(observed, "stalls", STALL)
    press_carriage(observed, "dissents", DISSENT)
    return observed.report()


if __name__ == "__main__":
    raise SystemExit(observe())
