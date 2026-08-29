"""Grade the four-lane shape in ``ROADMAP.md`` against ``contracts/roadmap-lanes.json``.

Every phase carries Now, Next, Needed and Never. The shape does not decay by
anyone arguing against it; it decays because the next editor writes a flat
paragraph, which is faster, and nothing notices. This module notices.

What it proves is presence, never truth. Whether a Now item can really be
finished with what exists today is judgement over evidence, and no parser
settles that. A green reading here means the four questions are still being
asked, not that the answers are right.

Never may not be empty. The other three may: a phase whose Now is empty is
saying that nothing in it can be finished yet, which is a reading worth
recording. An empty Never is not a reading, because a scope with no stated
edge has no edge.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "roadmap-lanes.json"

REFUSALS = {
    "ROADMAP_PHASE_MISSING_LANE":
        "A phase section in ROADMAP.md does not carry all four lanes.",
    "ROADMAP_EMPTY_NEVER":
        "A phase's Never lane is present but says nothing, so the scope has no stated edge.",
    "ROADMAP_LANE_VOCABULARY_DRIFT":
        "ROADMAP.md and contracts/roadmap-lanes.json no longer name the same four lanes.",
}

#: A phase heading: ``### `P0` · Ground and govern``. Only backticked phase ids
#: open a graded section, which is what keeps the prose sections that discuss
#: the lanes from being read as a phase that carries them.
PHASE_HEADING = re.compile(r"^#{2,3} `([FP]\d)` ·[^\n]*$", re.M)

#: A lane opener at the head of its own paragraph: ``**Never.** ...``.
LANE_OPENER = re.compile(r"^\*\*([A-Z][a-z]+)\.\*\*[ \n]", re.M)

#: Any bold-opened paragraph. A lane's prose ends at the next one of these, not
#: at the next lane: ``**Exits when**`` follows the last lane in every phase, and
#: bounding on lane openers alone let an emptied Never read as full.
BOLD_OPENER = re.compile(r"^\*\*", re.M)


class Defect(NamedTuple):
    """One refusal, named by its code and the exact thing that produced it."""

    code: str
    detail: str

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


def contract_lanes(contract: dict | None = None) -> list[str]:
    """The lane names the contract declares, in its declared order."""
    contract = contract if contract is not None else load_contract()
    return [str(lane["lane"]).title() for lane in contract.get("lanes") or []]


def lanes_that_may_be_empty(contract: dict | None = None) -> set[str]:
    """Lane names whose prose the contract admits as empty."""
    contract = contract if contract is not None else load_contract()
    return {str(lane["lane"]).title() for lane in contract.get("lanes") or []
            if lane.get("may_be_empty")}


def load_contract() -> dict:
    return json.loads(CONTRACT.read_bytes().decode("utf-8"))


def phase_sections(roadmap_text: str) -> dict[str, str]:
    """Phase id -> the body under its heading, up to the next heading."""
    sections: dict[str, str] = {}
    matches = list(PHASE_HEADING.finditer(roadmap_text))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(roadmap_text)
        body = roadmap_text[start:end]
        stop = re.search(r"^#{2,3} ", body, re.M)
        sections[match.group(1)] = body[:stop.start()] if stop else body
    return sections


def lanes_in(section: str) -> dict[str, str]:
    """Lane name -> its prose, for every ``**Name.**`` paragraph in one section."""
    found: dict[str, str] = {}
    boundaries = [match.start() for match in BOLD_OPENER.finditer(section)]
    for match in LANE_OPENER.finditer(section):
        start = match.end()
        after = [position for position in boundaries if position >= start]
        found[match.group(1)] = section[start:after[0] if after else len(section)].strip()
    return found


def grade(roadmap_text: str, contract: dict | None = None) -> list[Defect]:
    """Grade one roadmap's lane shape. Presence only; the readings are not judged."""
    contract = contract if contract is not None else load_contract()
    declared = contract_lanes(contract)
    optional = lanes_that_may_be_empty(contract)
    defects: list[Defect] = []
    sections = phase_sections(roadmap_text)

    carried: set[str] = set()
    for phase_id, section in sections.items():
        present = lanes_in(section)
        carried |= set(present) & set(declared)
        missing = [lane for lane in declared if lane not in present]
        if missing:
            defects.append(Defect(
                "ROADMAP_PHASE_MISSING_LANE",
                f"{phase_id} carries no {', '.join(missing)} lane"))
        for lane in declared:
            if lane in present and lane not in optional and not present[lane]:
                defects.append(Defect(
                    "ROADMAP_EMPTY_NEVER",
                    f"{phase_id} opens its {lane} lane and says nothing after it"))

    if sections and carried != set(declared):
        defects.append(Defect(
            "ROADMAP_LANE_VOCABULARY_DRIFT",
            f"the contract declares {', '.join(declared)}; the phases carry "
            f"{', '.join(sorted(carried)) or 'none of them'}"))
    return defects


def selfcheck() -> list[str]:
    """Prove every declared refusal fires against a controlled mutation."""
    contract = load_contract()
    declared = contract_lanes(contract)
    # The control ends on **Exits when**, the way every real phase does. Without
    # it the empty-Never mutation passes for the wrong reason: the last lane runs
    # to the end of the section and swallows whatever follows.
    admissible = "## The phases\n\n### `P0` · Control\n\n" + "\n\n".join(
        f"**{lane}.** A sentence." for lane in declared) + "\n\n**Exits when** it does.\n"
    failures = []
    if grade(admissible, contract):
        failures.append("the admissible control graded as defective")
    cases = {
        "ROADMAP_PHASE_MISSING_LANE": admissible.replace(
            f"**{declared[-1]}.** A sentence.\n", ""),
        "ROADMAP_EMPTY_NEVER": admissible.replace(
            f"**{declared[-1]}.** A sentence.", f"**{declared[-1]}.** "),
        "ROADMAP_LANE_VOCABULARY_DRIFT": admissible.replace(
            f"**{declared[0]}.**", "**Soon.**"),
    }
    for code, mutated in cases.items():
        if code not in {defect.code for defect in grade(mutated, contract)}:
            failures.append(f"{code} did not fire against its controlled mutation")
    return failures
