"""The numbers the snapshot states, and the record each one is derived from.

Split out of `scripts/sov_snapshot.py` on 2026-08-25 at the 300-line budget, and
split again on 2026-08-26 when Bdo's ruling on acceptance packet A5 moved the six
file-counting derivations onto the commit at HEAD. This half declares what the
page claims and names the source for each; `sovsnapshot/committed.py` owns every
call that reaches git, and the half next door grades a page against the answers
and is pure string work.

For eight of the ten claims the record is the commit and the page is the working
tree. That split is the ruling: the seven counts of committed files and the commit
count read what HEAD holds, so an untracked file belonging to a sibling session
cannot report a correct page as drifted, while `page_text` still reads `CLAUDE.md`
off disk so someone correcting a number is graded on the number they just wrote.
`committed.py` carries the reasoning and the consequence in the other direction.

Two claims deliberately did not move, and the ruling named them: `verification
checks` and `declared operations`. Each reads a number the repository already
computes - the check table `scripts/verify.py` itself imports, and the capability
map projection `scripts/sov_capability.py` builds and gates for staleness - so
putting them on the commit would mean parsing `git show HEAD:...` into a second
implementation of a count that already exists. That is how an earlier draft of
this check got 9 conformance cases against the suite's own 20. They read the
working tree, `UNCHECKED` says which half is which, and `sovsnapshot/shape.py`
holds them as named exceptions so a third one cannot join them quietly.

Every derivation can fail, and failing is not the same as the page being wrong. A
source that is missing, half-built, or unanswerable in this environment raises
`Underivable`, which the grader reports as "this is not a claim about the page".
Three separate rounds of witness dissent were needed to get that consistent
across every deriver: the guard kept being added to the one that had just failed
and not to its siblings.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, NamedTuple
import json

from sovsnapshot import committed
from sovsnapshot.committed import Underivable

#: This repository, resolved from where this file sits rather than from the
#: process working directory, for the same reason `committed.ROOT` is. Its own
#: constant and not `committed.ROOT`: an independent reading showed that reaching
#: the record module's `Path` and globbing it satisfies the structural guard next
#: door while reading the working tree, so `shape.py` now reports any reach of
#: `committed.ROOT` here and this module keeps the one line it needs.
ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "CLAUDE.md"

#: Claims the snapshot makes that this check does not verify, listed so silence is
#: never read as confirmation. Same inversion `scripts/sov_traps.py` uses.
#: This list was written from what someone remembered, not from the page. A
#: witness read every number in the snapshot section against the table below and
#: found three counts that were neither claimed nor listed - and two of them were
#: stale on the page while the check reported PASS, which is L-0001 happening
#: again inside the gate built to stop it. Everything cheaply and authoritatively
#: derivable is now a claim; what remains here is what this check genuinely
#: cannot settle.
UNCHECKED = (
    "conformance controlled cases - the suite counts differently from scenarios.json, "
    "and an earlier draft of this check got it wrong by re-counting",
    "wall-clock timings - these vary with machine load and sibling sessions",
    "every prose claim on the page - which services are built, which are boundary "
    "only, what is witnessed, what waits on Bdo. Numbers are all this check reads",
    "anything uncommitted, for the eight claims that count committed state - a "
    "source added, deleted or edited in the working tree is invisible to those "
    "until it lands. That is the referent Bdo ruled on in acceptance packet A5, "
    "and the cost of it is stated rather than left to be discovered",
    "whether `verification checks` and `declared operations` describe the commit - "
    "they do not. Those two read the working tree, because the repository already "
    "computes both numbers and reading them out of the commit would be a second "
    "implementation of a count that exists. So an uncommitted check, or a "
    "capability map built and not landed, moves them while HEAD stands still, and "
    "this check will report the page as drifted until that work lands",
)

#: The widest a tolerance may be. A tolerance absorbs the commits that land
#: between someone editing the page and someone running the check, which is tens
#: rather than hundreds; at 400 against a record of 356 the claim is vacuous and
#: nothing noticed. Absolute rather than a fraction of the live count, because a
#: fraction passes in a large repository and fails in a young one, and a check
#: whose verdict depends on which clone it runs in is telling you about the clone.
#: This is a tripwire against drift, not a wall against intent - the selfcheck
#: that reads it lives in the same module, so raising both is one edit. A
#: self-contained check cannot do better than make the drift visible.
MAX_TOLERANCE = 50


@dataclass(frozen=True)
class Claim:
    """One number the snapshot states, and how to find what it should be."""

    name: str
    pattern: str
    derive: Callable[[], int]
    tolerance: int = 0


def _verification_checks() -> int:
    """The declared check table is the source `scripts/verify.py` itself reads.

    Importing the module that holds the table is the whole derivation, which is why
    Bdo's ruling on acceptance packet A5 left this claim on the working tree:
    counting the same tuple out of `git show HEAD:...` would be a second
    implementation of a number `verify.py` already computes, and a second
    implementation is how a draft of this check got 9 conformance cases against the
    suite's own 20. What that costs is stated in `UNCHECKED`: a check added or
    removed and not yet committed moves this number while HEAD stands still.

    `ImportError` was the only guard, and a witness replaced `checks.py` with an
    unclosed parenthesis - which is what a shared working tree looks like while a
    sibling session is mid-edit - and got a `SyntaxError` traceback out of the
    check. A malformed check table is the environment failing to answer, not this
    module being wrong, so it refuses like any other unavailable source. The catch
    stays narrow for the reason the narrow guards exist: `except Exception` here
    would swallow a genuine defect in this module and report it as a bad checkout.
    """
    try:
        from sovverify.checks import CHECKS
    except (ImportError, SyntaxError, OSError) as missing:
        raise Underivable(f"the check table could not be read: {missing}") from missing
    return len(CHECKS)


def _decision_records() -> int:
    return committed.count("decisions", "[0-9]*.md", "decision records")


def _reports() -> int:
    return committed.count("reports", "*.md", "reports")


def _agent_definitions() -> int:
    return committed.count(".claude/agents", "*.md", "agent definitions")


def _skills() -> int:
    """One committed directory per skill, which is the count an untracked one moved.

    This is the claim the ruling was reproduced on: a sibling session creating
    `.claude/skills/<anything>/` turned the required gate red for every session on
    the branch, against an unmoved HEAD and a page that was correct.
    """
    return committed.count(".claude/skills", "*", "skills", dirs=True)


def _workflows() -> int:
    return committed.count(".claude/workflows", "*.js", "workflows")


def _service_manifests() -> int:
    """One `service.json` per bounded service, which is what a boundary is here.

    The page states this number twice, once as boundaries and once as manifests,
    and they are the same file counted the same way. Two claims over one derivation
    so that correcting one sentence and not the other is reported.
    """
    return committed.count_paths("services", "services/*/contracts/service.json",
                                 "service manifests")


def _declared_operations() -> int:
    """The capability map reference, which `sov_capability.py check` gates for staleness.

    An earlier version of this module declined to check this number, on the stated
    ground that re-counting it would be a second implementation. Both halves were
    wrong: no manifest carries a total, and this projection already holds the
    figure and is itself checked. Declining to derive what is cheaply and
    authoritatively derivable tells a reader the number cannot be reached when it
    can, which is its own kind of stale claim.

    Where the restraint does hold is the referent, and Bdo's ruling on acceptance
    packet A5 left this claim on the working tree for it: this file is the count,
    so running the same `json.loads(...)["capabilities"]` over committed bytes
    would move the source without removing the second implementation. What that
    costs is in `UNCHECKED`. `sov_capability.py build` writes this file, so a
    half-finished build is exactly when the check should say something intelligible
    rather than raise.
    """
    reference = ROOT / "contracts" / "fixtures" / "capability-map.reference.json"
    if not reference.is_file():
        raise Underivable("the capability map projection is absent; run "
                          "`python scripts/sov_capability.py build`")
    try:
        return len(json.loads(reference.read_text(encoding="utf-8"))["capabilities"])
    except (json.JSONDecodeError, KeyError, TypeError, OSError, UnicodeDecodeError) as broken:
        # OSError and UnicodeDecodeError are here because the neighbouring guard on
        # the page was written for the failure that had been demonstrated and not
        # for the one next to it. Same file, same read, same class of answer.
        raise Underivable(f"the capability map projection is unreadable: {broken}") from broken


#: Each pattern anchors on wording that appears once on the page. An earlier
#: version matched a bare "N commits," and found the historical count from day two
#: rather than the current one, reporting a correct page as drifted. Whitespace is
#: `\s+` throughout, because the page is markdown and a sentence wraps wherever
#: the line ends; literal spaces made three claims read as absent the moment the
#: paragraph reflowed, which reports a page as unverifiable rather than as wrong.
CLAIMS = (
    Claim("verification checks", r"runs\s+(\d+)\s+checks", _verification_checks),
    Claim("commits", r"it\s+now\s+holds\s+(\d+)\s+commits", committed.commits, tolerance=25),
    Claim("decision records",
          r"it\s+now\s+holds\s+\d+\s+commits,\s+(\d+)\s+decision\s+records",
          _decision_records),
    Claim("declared operations", r"(\d+)\s+declared\s+operations", _declared_operations),
    Claim("service boundaries", r"(\d+)\s+service\s+boundaries", _service_manifests),
    Claim("manifests", r"across\s+(\d+)\s+manifests", _service_manifests),
    Claim("agent definitions", r"(\d+)\s+agent\s+definitions", _agent_definitions),
    Claim("skills", r"(\d+)\s+skills", _skills),
    Claim("workflows", r"(\d+)\s+workflows", _workflows),
    Claim("reports",
          r"it\s+now\s+holds\s+\d+\s+commits,\s+\d+\s+decision\s+records\s+and\s+"
          r"(\d+)\s+reports",
          _reports),
)


class Derived(NamedTuple):
    """What this environment could answer, and why it could not answer the rest."""

    values: dict[str, int]
    reasons: dict[str, str]


def page_text() -> str:
    """The snapshot page, read from the working tree, which is the deliberate one.

    Eight of the ten counts are of the commit at HEAD; this is not, and the
    asymmetry is the point. Grading the committed page would tell someone who has
    just corrected a number that it is still wrong, which is the same unactionable
    verdict the ruling removed from the other direction.

    It is a source like any other and can be missing. Every deriver was taught to
    refuse rather than raise; the page was not, because the grader read it
    directly, so a tree without `CLAUDE.md` produced a `FileNotFoundError`
    traceback out of the one check whose whole purpose is to report on that file.
    The reader this check exists for was the last source with no guard.
    """
    if not SNAPSHOT.exists():
        raise Underivable(f"the snapshot page is absent: no {SNAPSHOT.name} here")
    if not SNAPSHOT.is_file():
        # "Absent" named a cause this guard had not established. A directory of
        # that name is present and unreadable, which is a different sentence.
        raise Underivable(f"{SNAPSHOT.name} is present but is not a file")
    try:
        return SNAPSHOT.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as unreadable:
        # Existence was guarded and readability was not. A Windows editor saving
        # UTF-16 produced a `UnicodeDecodeError` traceback out of the check whose
        # subject is that file - the guard built for the demonstrated failure and
        # not its neighbour, one round after that lesson was written down.
        raise Underivable(f"the snapshot page cannot be read: {unreadable}") from unreadable


def derive_all() -> Derived:
    """Answer every claim this environment can, once per pass.

    Once, not per grading call: several sessions share this working tree, and
    re-deriving inside each call let a sibling writing a report change the answer
    between two cases, which reported the check as broken when the record had
    simply moved. Reading the commit rather than the tree removes most of that
    race, and `committed.one_reading` removes the rest of it inside a pass: seven
    of the ten claims read the same listing, and they must all read the same one.

    A pass, not a command. `sov_snapshot.cmd_check` calls this twice - once so the
    selfcheck can prove the grader works, once to grade the page - and those are
    two readings of the commit. Nothing is printed here; each caller words its own
    report.
    """
    values: dict[str, int] = {}
    reasons: dict[str, str] = {}
    with committed.one_reading():
        for claim in CLAIMS:
            try:
                values[claim.name] = claim.derive()
            except Underivable as missing:
                reasons[claim.name] = str(missing)
    return Derived(values, reasons)
