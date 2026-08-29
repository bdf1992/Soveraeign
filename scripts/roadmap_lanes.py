"""Grade the four-lane shape in ``ROADMAP.md`` against ``contracts/roadmap-lanes.json``.

Every graded subject carries Now, Next, Needed and Never. The shape does not
decay by anyone arguing against it; it decays because the next editor writes a
flat paragraph, which is faster, and nothing notices. This module notices.

What it proves is presence, never truth. Whether a Now item can really be
finished with what exists today is judgement over evidence, and no parser
settles that. A green reading here means the four questions are still being
asked, not that the answers are right.

Never may not be empty. The other three may: a subject whose Now is empty is
saying that nothing in it can be finished yet, which is a reading worth
recording. An empty Never is not a reading, because a scope with no stated
edge has no edge.

Three rules earned by a witness defeating the first draft, kept here because
each names a class rather than the instance that found it. A lane's prose is
its own paragraph and stops at the blank line, so the first draft's bound on
the *next bold paragraph* no longer lets an italic follower be swallowed. A
lane that opens twice is refused rather than resolved last-wins, which had let
a duplicate mask an emptied original. And the graded subjects are cross-checked
against the roadmap's own phase table, so a mistyped heading is named instead
of quietly removing a phase from the population.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "roadmap-lanes.json"

REFUSALS = {
    "ROADMAP_SUBJECT_MISSING_LANE":
        "A graded subject in ROADMAP.md does not carry all four lanes.",
    "ROADMAP_EMPTY_NEVER":
        "A Never lane carries no substantive prose, so the scope has no stated edge.",
    "ROADMAP_LANE_DECLARED_TWICE":
        "One subject opens the same lane twice, which lets the second mask the first.",
    "ROADMAP_UNDECLARED_LANE":
        "A subject opens a lane-shaped paragraph the contract declares neither as a lane "
        "nor as an admitted non-lane opener.",
    "ROADMAP_PHASE_NOT_GRADED":
        "The roadmap's phase table names a phase with no graded section, so a mistyped "
        "heading would drop it from the population unseen.",
}

#: A phase heading. Multi-digit and optional backticks, so a `P10` section and a
#: mistyped backtick are both visible; the first draft matched one digit and a
#: required backtick, and a new phase or a typo went unread by the grader while
#: staying visible to ``sov_next``.
#:
#: `P` only. The archived `F0`-`F6` ladder carries no lanes and must not be made
#: to: ``ROADMAP-F0-F6.md`` is pinned byte-for-byte in ``contracts/phases.json``
#: as the definition the closed `phase:i` was graded against, so a check that
#: demanded lanes there would demand editing a closed phase's definition.
PHASE_HEADING = re.compile(r"^#{2,3} `?(P\d+)`? ·[^\n]*$", re.M)

#: A row of the phase table: ``| `P0` Ground and govern | ... |``.
PHASE_TABLE_ROW = re.compile(r"^\| `(P\d+)` ", re.M)

#: A lane opener at the head of its own paragraph: ``**Never.** ...``.
LANE_OPENER = re.compile(r"^\*\*([A-Z][a-z]+)\.\*\*(?=[ \n])", re.M)

#: Blockquote markers, stripped before parsing a subject that declares them.
BLOCKQUOTE = re.compile(r"^> ?", re.M)


class Defect(NamedTuple):
    """One refusal, named by its code and the exact thing that produced it."""

    code: str
    detail: str

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


def load_contract() -> dict:
    return json.loads(CONTRACT.read_bytes().decode("utf-8"))


def contract_lanes(contract: dict | None = None) -> list[str]:
    """The lane names the contract declares, in its declared order."""
    contract = contract if contract is not None else load_contract()
    return [str(lane["lane"]).title() for lane in contract.get("lanes") or []]


def lanes_that_may_be_empty(contract: dict | None = None) -> set[str]:
    """Lane names whose prose the contract admits as empty."""
    contract = contract if contract is not None else load_contract()
    return {str(lane["lane"]).title() for lane in contract.get("lanes") or []
            if lane.get("may_be_empty")}


def _body(text: str, start: int) -> str:
    """The text from ``start`` up to the next heading of any level."""
    rest = text[start:]
    stop = re.search(r"^#{1,6} ", rest, re.M)
    return rest[:stop.start()] if stop else rest


def graded_subjects(roadmap_text: str, contract: dict | None = None) -> dict[str, str]:
    """Subject label -> the body graded for lanes.

    Every phase heading, plus the extra headings the contract names. The extras
    are how the recursion gets graded at all: the roadmap's own lanes and the
    worked child are declared by the same contract to carry the same shape, and
    a check that read only phase sections would grade one level of a rule that
    claims to hold at every level.
    """
    contract = contract if contract is not None else load_contract()
    subjects = {match.group(1): _body(roadmap_text, match.end())
                for match in PHASE_HEADING.finditer(roadmap_text)}
    for extra in (contract.get("graded_subjects") or {}).get("extra") or []:
        heading = str(extra.get("heading"))
        found = re.search(rf"^#{{2,4}} {re.escape(heading)}\s*$", roadmap_text, re.M)
        if not found:
            continue
        body = _body(roadmap_text, found.end())
        subjects[str(extra.get("subject") or heading)] = (
            BLOCKQUOTE.sub("", body) if extra.get("strip_blockquote") else body)
    return subjects


def phase_sections(roadmap_text: str) -> dict[str, str]:
    """Phase id -> the body under its heading. Kept for readers that want phases only."""
    return {match.group(1): _body(roadmap_text, match.end())
            for match in PHASE_HEADING.finditer(roadmap_text)}


def table_phases(roadmap_text: str) -> list[str]:
    """Phase ids the roadmap's tables name, first mention first.

    The name crosswalk keys its rows onto the same ladder, so a phase is named
    more than once. Deduplicated rather than filtered by section: a phase in
    either table with no graded heading is the same defect.
    """
    seen: dict[str, None] = {}
    for match in PHASE_TABLE_ROW.finditer(roadmap_text):
        seen.setdefault(match.group(1), None)
    return list(seen)


def lanes_in(section: str) -> dict[str, list[str]]:
    """Lane name -> the prose of every paragraph that opens it.

    A lane's prose is its own paragraph and ends at the blank line. Bounding on
    the next *bold* paragraph instead let a lane swallow an italic follower, so
    an emptied Never sitting above ``*Repository reading.*`` read as full.

    The value is a list because a lane opening twice is a defect the caller
    refuses. Returning the last one silently is what let a duplicate mask an
    emptied original.
    """
    found: dict[str, list[str]] = {}
    for match in LANE_OPENER.finditer(section):
        rest = section[match.end():]
        end = rest.find("\n\n")
        found.setdefault(match.group(1), []).append(
            (rest if end < 0 else rest[:end]).strip())
    return found


def _words(prose: str) -> int:
    """Words of substance, so a lone full stop does not read as a stated edge.

    The threshold is deliberately low. It refuses a lane opened and abandoned;
    it never grades how well an edge is written, because that is a reading.
    """
    return len(re.findall(r"[0-9A-Za-z][0-9A-Za-z'-]*", prose))


def grade(roadmap_text: str, contract: dict | None = None) -> list[Defect]:
    """Grade one roadmap's lane shape. Presence only; the readings are not judged."""
    contract = contract if contract is not None else load_contract()
    declared = contract_lanes(contract)
    optional = lanes_that_may_be_empty(contract)
    admitted = set((contract.get("graded_subjects") or {}).get("admitted_non_lane_openers") or [])
    minimum = int(contract.get("never_minimum_words") or 1)
    defects: list[Defect] = []
    subjects = graded_subjects(roadmap_text, contract)

    for label in table_phases(roadmap_text):
        if label not in subjects:
            defects.append(Defect(
                "ROADMAP_PHASE_NOT_GRADED",
                f"the phase table names {label}, which has no graded section"))

    for label, section in subjects.items():
        present = lanes_in(section)
        missing = [lane for lane in declared if lane not in present]
        if missing:
            defects.append(Defect(
                "ROADMAP_SUBJECT_MISSING_LANE",
                f"{label} carries no {', '.join(missing)} lane"))
        for lane, occurrences in present.items():
            if lane not in declared and lane not in admitted:
                defects.append(Defect(
                    "ROADMAP_UNDECLARED_LANE",
                    f"{label} opens a {lane} paragraph, which is neither a lane nor "
                    "an admitted non-lane opener"))
                continue
            if lane in declared and len(occurrences) > 1:
                defects.append(Defect(
                    "ROADMAP_LANE_DECLARED_TWICE",
                    f"{label} opens its {lane} lane {len(occurrences)} times"))
            if lane in declared and lane not in optional:
                if _words(occurrences[0]) < minimum:
                    defects.append(Defect(
                        "ROADMAP_EMPTY_NEVER",
                        f"{label} opens its {lane} lane and says nothing after it"))
    return defects


CONTROL = """## The phases

| Phase | Product result | Estimate |
| --- | --- | ---: |
| `P0` Control | A product result | 50% |

### `P0` · Control

**Result.** A product result.

{lanes}

*Repository reading.* A reading that follows the lanes.

**Exits when** it does.

### The roadmap's own lanes

{lanes}
"""


def _control(contract: dict) -> str:
    lanes = "\n\n".join(f"**{lane}.** A sentence of four words."
                        for lane in contract_lanes(contract))
    return CONTROL.format(lanes=lanes)


def selfcheck() -> list[str]:
    """Prove every declared refusal fires alone against a controlled mutation."""
    contract = load_contract()
    declared = contract_lanes(contract)
    last, first = declared[-1], declared[0]
    admissible = _control(contract)
    failures = []
    if grade(admissible, contract):
        failures.append(f"the admissible control graded as defective: "
                        f"{[str(d) for d in grade(admissible, contract)]}")
    cases = {
        # Drop the last lane from the phase only, so the roadmap subject stays whole.
        "ROADMAP_SUBJECT_MISSING_LANE": admissible.replace(
            f"**{last}.** A sentence of four words.", "", 1),
        # A lone full stop is not a stated edge, and it sits above an italic
        # paragraph, which is the shape that defeated the first draft.
        "ROADMAP_EMPTY_NEVER": admissible.replace(
            f"**{last}.** A sentence of four words.", f"**{last}.** .", 1),
        "ROADMAP_LANE_DECLARED_TWICE": admissible.replace(
            f"**{last}.** A sentence of four words.",
            f"**{last}.** A sentence of four words.\n\n**{last}.** Another four words here.",
            1),
        "ROADMAP_UNDECLARED_LANE": admissible.replace(
            f"**{first}.** A sentence of four words.",
            f"**{first}.** A sentence of four words.\n\n**Soon.** A sentence of four words.",
            1),
        "ROADMAP_PHASE_NOT_GRADED": admissible.replace("### `P0` · Control", "### P0 - Control"),
    }
    for code, mutated in cases.items():
        fired = {defect.code for defect in grade(mutated, contract)}
        if code not in fired:
            failures.append(f"{code} did not fire against its controlled mutation")
        elif fired != {code}:
            failures.append(f"{code} fired with {sorted(fired - {code})}; it must fire alone")
    return failures
