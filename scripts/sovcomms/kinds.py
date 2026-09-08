"""The three claims a Communications surface makes that a record can refute.

Each kind extracts a claim and compares it against something that owns it. None
of them grades phrasing: a word list would be a declared case pretending to be a
net, which is why two kinds were withdrawn from `scripts/sov_harness.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import subprocess
import sys

#: A quantified claim about behaviour, not an ordinary count of things. Both a
#: number and one of these markers must appear in the same sentence before the
#: paragraph is asked for its source, which is what keeps "60 agent invocations"
#: in a grant description out of the population this grades.
MEASURE_MARKER = re.compile(
    r"\b(measured|measurement|measurements|on average|averaged?|median|percent|"
    r"turns?|sessions?|tool calls?|invocations measured|runs\b|times\b|"
    r"of all|of his|of her|of their|of the ten|of the twenty)\b",
    re.I)

#: Digits, or a spelled cardinal. Spelled forms are how "seven sessions" and
#: "Six of the ten largest repair commits" evaded a digit-only reading.
NUMBER = re.compile(
    r"(?<![\w.])(\d[\d,]*(?:\.\d+)?%?|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)(?![\w])",
    re.I)

#: What counts as naming the thing that PRODUCES a figure: something runnable.
#: A cited document is a citation, not a producer, and the first version of this
#: pattern accepted one - which let four of the five statistics that motivated
#: this grader through, because their paragraphs each happened to backtick a
#: filename. Naming `verify.py` does not derive "1,768 times".
SOURCE_MARKER = re.compile(
    r"(python scripts/[a-z_]+\.py|`python [^`]+`|\bscripts/[a-z_]+\.py\b|"
    r"`git (?:log|rev-list|status|diff|show|branch)\b)",
    re.I)

#: Machine vocabulary. A person reading one of these has to translate it, which
#: is the whole reason the Communications seat exists.
INTERNAL_TOKENS = (
    "WITNESSED", "RATIFIED", "UNATTESTABLE", "RECORD_DEFECT", "WORK_DEFECT",
    "WORKER_DEFECT", "ORCHESTRATION_DEFECT", "WITNESS_DEFECT", "POLICY_SEAM",
    "AUTHORITY_SEAM", "EFFECT_SEAM", "DEPENDENCY_SEAM", "ACCEPTANCE_SEAM",
    "RECORD_LOCAL", "RESOURCE_CONSUMPTION", "RESOURCE_COMMITMENT",
    "EXTERNAL_WORLD", "PREAPPROVAL_REQUESTED", "OWNER_HELD", "UNROUTED",
    "CLOSED_INCOMPLETE", "NONE_ACTIVE", "FINDING_SET", "PARTICIPANT_IN_WORK",
)

#: A standing token preceded by NOT is a denial, not a claim. NOT_WITNESSED
#: contains WITNESSED and a substring reading reports every unwitnessed subject
#: in the repository as witnessed (CLAUDE.md trap T3).
STANDING_CLAIM = re.compile(
    r"(?<![A-Z_])(NOT_)?(WITNESSED|RATIFIED)(?![A-Z_])")


@dataclass(frozen=True)
class Defect:
    """One Communications claim the record it names does not support."""

    kind: str
    where: str
    detail: str

    def __str__(self) -> str:
        return f"{self.kind:<20} {self.where}\n{' ' * 21}{self.detail}"


def paragraphs(text: str) -> list[tuple[int, str]]:
    """Split into paragraphs, each with the 1-indexed line its first line is on."""
    out: list[tuple[int, str]] = []
    line_no, buf, start = 1, [], 1
    for raw in text.splitlines():
        if raw.strip():
            if not buf:
                start = line_no
            buf.append(raw)
        elif buf:
            out.append((start, "\n".join(buf)))
            buf = []
        line_no += 1
    if buf:
        out.append((start, "\n".join(buf)))
    return out


def _sentences(block: str) -> list[str]:
    """Split a paragraph into sentences without importing a tokenizer."""
    flat = " ".join(block.split())
    return [s for s in re.split(r"(?<=[.!?])\s+", flat) if s]


#: How near a marker must sit to its number, in words. A quantified claim reads
#: as one phrase - "379 of his turns", "68 measured sessions", "1,768 times" - so
#: proximity is what separates a claim from a grammatical collision. Without it,
#: "When you write one, make it re-derive from bytes at the moment it runs" reads
#: as a measurement, and a grader that cries wolf is turned off.
ADJACENT_WORDS = 3


def _quantified(sentence: str) -> tuple[str, str] | None:
    """The first number sitting within ADJACENT_WORDS of a measurement marker."""
    words = sentence.split()
    numbers = [(i, w) for i, w in enumerate(words) if NUMBER.fullmatch(w.strip(".,;:()'\""))]
    for index, word in numbers:
        window = words[max(0, index - ADJACENT_WORDS):index + ADJACENT_WORDS + 1]
        marker = MEASURE_MARKER.search(" ".join(window))
        if marker:
            return word.strip(".,;:()'\""), marker.group(0)
    return None


def check_unsourced_number(where: str, text: str,
                           historical: frozenset[str] = frozenset()) -> list[Defect]:
    """A behavioural figure whose paragraph names nothing that produces it.

    `historical` holds sentences the contract records as statements about a past
    state or about a claim that was removed. Grading those would demand editing
    the record of what was once true, which is the exemption
    `scripts/sov_harness.py` makes for drafts and `counted-populations.json`
    makes for dated readings.
    """
    defects: list[Defect] = []
    for line_no, block in paragraphs(text):
        if SOURCE_MARKER.search(block):
            continue
        for sentence in _sentences(block):
            if any(marker in sentence for marker in historical):
                continue
            found = _quantified(sentence)
            if not found:
                continue
            number, marker = found
            defects.append(Defect(
                "UNSOURCED_FIGURE", f"{where}:{line_no}",
                f"states {number!r} against {marker!r} and its paragraph "
                f"names no command, script or record that produces it"))
            break
    return defects


#: A gloss: the token, a marker, and at least two words of plain English. Progressive
#: disclosure rather than prohibition - "WITNESSED (independently confirmed)" teaches a
#: reader the vocabulary this repository actually runs on, while forbidding the token
#: outright would leave them unable to read anything else here. Only the first use is
#: asked for one; a reader who has been told once does not need telling again.
GLOSS = r"\s*[(\[\u2014\u2013:,-]\s*\w+\W+\w+"


def check_unglossed_token(where: str, text: str) -> list[Defect]:
    """A machine type used in front of a person without ever saying what it means."""
    defects: list[Defect] = []
    for token in INTERNAL_TOKENS:
        bare = re.compile(rf"(?<![A-Za-z_]){token}(?![A-Za-z_])")
        glossed = re.compile(rf"(?<![A-Za-z_]){token}(?![A-Za-z_]){GLOSS}")
        first = None
        for index, line in enumerate(text.splitlines(), start=1):
            if bare.search(line):
                first = (index, line)
                break
        if first and not glossed.search(first[1]):
            defects.append(Defect(
                "UNGLOSSED_TOKEN", f"{where}:{first[0]}",
                f"{token} is a machine type and this is its first use; gloss it once, as "
                f"{token} (what it means), then use it freely"))
    return sorted(defects, key=lambda d: int(d.where.rsplit(":", 1)[1]))


def supported_standing(root) -> set[str]:
    """Subjects `sov_standing.py` reports as supported, read from its own output."""
    try:
        run = subprocess.run([sys.executable, "scripts/sov_standing.py"], cwd=root,
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return set()
    supported = set()
    for line in run.stdout.splitlines():
        parts = line.split()
        if parts and parts[0] == "SUPPORTED" and len(parts) > 1:
            supported.add(parts[1])
    return supported


def check_unsupported_standing(where: str, text: str, supported: set[str]) -> list[Defect]:
    """A WITNESSED or RATIFIED claim naming a subject the witness records do not carry."""
    defects: list[Defect] = []
    for index, line in enumerate(text.splitlines(), start=1):
        for match in STANDING_CLAIM.finditer(line):
            if match.group(1):
                continue
            subjects = re.findall(r"\b([a-z][a-z0-9_]*_status)\b", line)
            named = [s for s in subjects if s not in supported]
            if not named:
                continue
            defects.append(Defect(
                "UNSUPPORTED_STANDING", f"{where}:{index}",
                f"claims {match.group(2)} for {', '.join(named)}; "
                f"python scripts/sov_standing.py does not support it"))
    return defects
