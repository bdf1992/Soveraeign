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

This module owns the contract and the refusals. ``roadmap_document`` owns how
the document is read.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple
import json

from roadmap_document import (
    extras,
    graded_subjects,
    lanes_in,
    phase_sections,
    table_phases,
    words,
)

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
    "ROADMAP_SUBJECT_NOT_FOUND":
        "The contract declares an extra graded subject by heading, and no such heading "
        "exists, so renaming one would silently stop grading it.",
    "ROADMAP_SUBJECT_HEADING_AMBIGUOUS":
        "Two headings answer to one declared subject, so which one is graded depends on "
        "document order.",
}


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


def subjects_of(roadmap_text: str, contract: dict | None = None) -> dict[str, str]:
    """Every graded subject, resolved against the contract."""
    return graded_subjects(roadmap_text, contract if contract is not None else load_contract())


def _population(roadmap_text: str, contract: dict) -> list[Defect]:
    """Defects about which subjects exist at all, before any lane is read."""
    defects = []
    subjects = graded_subjects(roadmap_text, contract)
    for label in table_phases(roadmap_text):
        if label not in subjects:
            defects.append(Defect(
                "ROADMAP_PHASE_NOT_GRADED",
                f"the phase table names {label}, which has no graded section"))
    for extra, found in extras(roadmap_text, contract):
        if not found:
            defects.append(Defect(
                "ROADMAP_SUBJECT_NOT_FOUND",
                f"the contract grades {extra.get('subject')!r} under the heading "
                f"{extra.get('heading')!r}, which the document does not carry"))
        elif len(found) > 1:
            defects.append(Defect(
                "ROADMAP_SUBJECT_HEADING_AMBIGUOUS",
                f"{len(found)} headings read {extra.get('heading')!r}, so which one is "
                f"graded as {extra.get('subject')!r} depends on document order"))
    return defects


def _lanes(label: str, section: str, contract: dict) -> list[Defect]:
    """Defects about the four lanes of one subject."""
    declared = contract_lanes(contract)
    optional = lanes_that_may_be_empty(contract)
    admitted = set((contract.get("graded_subjects") or {}).get("admitted_non_lane_openers") or [])
    minimum = int(contract.get("never_minimum_words") or 1)
    defects = []
    present = lanes_in(section)
    missing = [lane for lane in declared if lane not in present]
    if missing:
        defects.append(Defect(
            "ROADMAP_SUBJECT_MISSING_LANE",
            f"{label} carries no {', '.join(missing)} lane"))
    for lane, occurrences in present.items():
        if lane not in declared:
            if lane not in admitted:
                defects.append(Defect(
                    "ROADMAP_UNDECLARED_LANE",
                    f"{label} opens a {lane} paragraph, which is neither a lane nor "
                    "an admitted non-lane opener"))
            continue
        if len(occurrences) > 1:
            defects.append(Defect(
                "ROADMAP_LANE_DECLARED_TWICE",
                f"{label} opens its {lane} lane {len(occurrences)} times"))
        if lane not in optional and words(occurrences[0]) < minimum:
            defects.append(Defect(
                "ROADMAP_EMPTY_NEVER",
                f"{label} opens its {lane} lane and its own paragraph carries "
                f"fewer than {minimum} words"))
    return defects


def grade(roadmap_text: str, contract: dict | None = None) -> list[Defect]:
    """Grade one roadmap's lane shape. Presence only; the readings are not judged."""
    contract = contract if contract is not None else load_contract()

    # A text carrying no `P` phase at all is not the document this grades: the
    # archived F-ladder and the small fixtures the signpost reconciler uses are
    # both legitimately laneless. Demanding the contract's extra subjects of them
    # would refuse a document that never claimed the shape. If the live roadmap
    # ever loses every phase, `sov_next` still refuses it - its crosswalk rows
    # name phases that would then resolve to nothing.
    if not phase_sections(roadmap_text) and not table_phases(roadmap_text):
        return []

    defects = _population(roadmap_text, contract)
    for label, section in graded_subjects(roadmap_text, contract).items():
        defects.extend(_lanes(label, section, contract))
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

### The shape recurses

Prose about the recursion.

> **A worked child.**
>
{quoted}

### The roadmap's own lanes

{lanes}
"""


def control(contract: dict) -> str:
    """A whole small roadmap carrying every graded subject the contract declares.

    Including the blockquoted child: without it the strip_blockquote path has no
    controlled case, and the extras are exercised only against the live document.
    It also ends its phase on an italic paragraph, which is the follower shape
    that defeated the first two drafts of the empty-Never rule.
    """
    sentences = [f"**{lane}.** A sentence of four words." for lane in contract_lanes(contract)]
    return CONTROL.format(
        lanes="\n\n".join(sentences),
        quoted="\n>\n".join(f"> {sentence}" for sentence in sentences))


def selfcheck() -> list[str]:
    """Prove every declared refusal fires alone against a controlled mutation."""
    contract = load_contract()
    declared = contract_lanes(contract)
    last, first = declared[-1], declared[0]
    admissible = control(contract)
    sentence = f"**{last}.** A sentence of four words."
    failures = []
    if grade(admissible, contract):
        failures.append("the admissible control graded as defective: "
                        f"{[str(defect) for defect in grade(admissible, contract)]}")
    cases = {
        # Each mutation touches the phase only, so the other subjects stay whole
        # and the refusal under test is the only one that can fire.
        "ROADMAP_SUBJECT_MISSING_LANE": admissible.replace(sentence, "", 1),
        "ROADMAP_EMPTY_NEVER": admissible.replace(sentence, f"**{last}.** .", 1),
        "ROADMAP_LANE_DECLARED_TWICE": admissible.replace(
            sentence, f"{sentence}\n\n**{last}.** Another four words here.", 1),
        "ROADMAP_UNDECLARED_LANE": admissible.replace(
            f"**{first}.** A sentence of four words.",
            f"**{first}.** A sentence of four words.\n\n**Soon.** A sentence of four words.",
            1),
        "ROADMAP_PHASE_NOT_GRADED": admissible.replace("### `P0` · Control", "### P0 - Control"),
        "ROADMAP_SUBJECT_NOT_FOUND": admissible.replace(
            "### The shape recurses", "### How the shape recurses"),
        "ROADMAP_SUBJECT_HEADING_AMBIGUOUS": admissible.replace(
            "### The roadmap's own lanes",
            "### The roadmap's own lanes\n\nText.\n\n### The roadmap's own lanes", 1),
    }
    for code, mutated in cases.items():
        fired = {defect.code for defect in grade(mutated, contract)}
        if code not in fired:
            failures.append(f"{code} did not fire against its controlled mutation")
        elif fired != {code}:
            failures.append(f"{code} fired with {sorted(fired - {code})}; it must fire alone")
    return failures
