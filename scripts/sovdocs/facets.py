"""Classify each document by facets this repository already carries.

Nothing here invents a taxonomy. `AGENTS.md` already says what each directory
owns, `contracts/capability-offices.json` already sorts operations into offices
and counters, `.claude/epic/villages.json` already sorts domains into villages,
and 91 documents already declare their own standing in a `Status:` line. A ninth
grouping written into a viewer would be a second vocabulary competing with those
(`AGENTS.md`, Design System of Record).

The facets compose rather than nesting. A charter is a `charter`, inside the
`record` boundary, at `BUILT` standing, met at the `BACK` office, all at once; a
single tree would force a false choice between those.

There is no catch-all. A document no rule claims raises `Unclassified`, which
fails the documentation check and names the file. A default bucket is how a
taxonomy quietly stops being true, and this corpus grew from 156 documents to
158 in one afternoon.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re


# Kind is read from where a document sits and what it is named, because that is
# what the repository already uses to mean these things. First match wins, so the
# specific rules come before the general ones.
KIND_RULES: tuple[tuple[str, str, str], ...] = (
    (r"decisions/\d{4}-[a-z0-9-]+\.md$", "decision", "A consequential choice, its rationale and consequences."),
    (r"reports/\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$", "report", "What one run or pass observed. Never policy."),
    (r"(^|/)PROD-[A-Z0-9-]+-BUILD\.md$", "report", "What one run or pass observed. Never policy."),
    (r"(^|/)CHARTER\.md$", "charter", "What a service boundary owns and refuses."),
    (r"(^|/)SRD\.md$", "srd",
     "What a service's own caller needs from it, at the fidelity PRD.md gives the Node."),
    (r"(^|/)SERVICE-SPEC\.md$", "service-spec",
     "What a service must therefore do, stated so a caller can be held to it."),
    (r"(^|/)SERVICE-GROUND\.md$", "service-ground",
     "What is true of a service today, as distinct from what it is for."),
    (r"(^|/)JOURNEYS\.md$", "journeys",
     "One caller's path through a service, end to end, with what it meets."),
    (r"(^|/)KNOWN-GAPS\.md$", "known-gaps", "What a service has not built yet, stated by the service."),
    (r"(^|/)PARITY\.md$", "known-gaps", "A parity ledger: what a boundary has not reached yet."),
    (r"(^|/)BASELINE\.md$", "baseline", "A recorded grading a participant is measured against."),
    (r"(^|/)INTEGRATING\.md$", "guide",
     "How to add the next one of a thing, written from what the existing ones do."),
    (r"\.claude/skills/[^/]+/SKILL\.md$", "skill", "Domain know-how loaded for one kind of task."),
    (r"\.claude/agents/[^/]+\.md$", "agent", "A stable role an operator can launch."),
    (r"\.claude/workflows/[^/]+\.md$", "workflow", "A launchable multi-step run."),
    (r"\.claude/epic/[^/]+\.md$", "narrative", "The story layer over the epic tree."),
    (r"\.claude/controllers/[^/]+\.md$", "agent",
     "A stable role an operator can launch."),
    (r"\.claude/register/[^/]+\.md$", "register",
     "How to hand one named participant a result they can act on."),
    (r"diagrams/[^/]+\.md$", "diagram", "A picture of one mechanism, with its source."),
    (r"infrastructure/[^/]+\.md$", "infrastructure", "How the node itself is provisioned and witnessed."),
    (r"\.github/[^/]+\.md$", "template", "A form the coordination surface fills in."),
    (r"(^|/)README\.md$", "readme", "Orientation for one directory."),
    (r"^archives/[^/]+\.md$", "archived",
     "A superseded governing document, kept byte-identical. Never current policy."),
    (r"^witness/[^/]+\.md$", "witness",
     "An observation of an artifact by something that did not build it."),
    (r"^[A-Z][A-Za-z0-9-]*\.md$", "governing", "Part of the design System of Record."),
)

# Excluded from the published corpus rather than left unclassified. Drafts are
# work in progress an author has not offered to a reader; excluding them is a
# reversible default, and `sov_docs.py` refuses a document that is neither
# classified nor excluded.
#
# Any `drafts/` directory, not only the harness's own: a draft written beside the
# work it is about is still a draft, and naming the directory is how an author says
# so. Written as the general rule when an experiment's design notes landed in the
# corpus and failed the reader for every session sharing this tree.
EXCLUDED = (r"(^|/)drafts/",)

# `AGENTS.md` (Directory boundaries) names what each of these owns. This is the
# projection of that table; `boundary_drift` refuses when the two disagree.
BOUNDARIES: tuple[tuple[str, str], ...] = (
    ("contracts/", "contracts"),
    ("conformance/", "conformance"),
    ("services/", "services"),
    ("bindings/", "bindings"),
    ("adapters/", "adapters"),
    ("workers/", "workers"),
    ("scripts/", "scripts"),
    ("acceptance/", "acceptance"),
    ("archives/", "archives"),
    ("decisions/", "decisions"),
    ("lineage/", "lineage"),
)

STATUS_LINE = re.compile(r"^Status:\s*`?([^`\n]+?)`?\s*$", re.M)
UNSTATED = "unstated"

# Standing is written in prose here, in about thirty phrasings across 91
# documents. These grade it, first match winning, most decisive first: a record
# that is both owner-directed and a freeze candidate is a candidate, and one that
# is both directed and ruled is ruled. A phrasing none of these claim is NOT
# pooled into an "other" bucket - it keeps its own words and appears as its own
# filter value, so a new phrasing shows itself rather than disappearing.
GRADES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("superseded", ("SUPERSEDED", "WITHDRAWN", "RETIRED")),
    ("ratified", ("RATIFIED",)),
    ("accepted", ("ACCEPT", "RULED")),
    ("built", ("BUILT", "EXECUTABLE", "EXPERIMENTAL")),
    ("proposed", ("PROPOS", "CHARTERED", "CANDIDATE", "PROVISIONAL", "DRAFT")),
    ("directed", ("OWNER-DIRECTED", "OWNER-SELECTED", "OWNER_DIRECTED", "DIRECTED")),
)


class Unclassified(RuntimeError):
    """A document no kind rule claims and no exclusion covers."""


def excluded(path: str) -> bool:
    """Whether this document is deliberately outside the published corpus."""
    return any(re.search(pattern, path) for pattern in EXCLUDED)


def kind(path: str) -> str:
    """The sort of document this is, from where it sits and what it is named."""
    for pattern, name, _ in KIND_RULES:
        if re.search(pattern, path):
            return name
    raise Unclassified(
        f"{path} matches no kind rule and no exclusion; add a rule in "
        "scripts/sovdocs/facets.py or exclude it deliberately")


def kind_note(name: str) -> str:
    """The one-line gloss for a kind, so a reader never meets a bare label."""
    for _, candidate, note in KIND_RULES:
        if candidate == name:
            return note
    return ""


def boundary(path: str) -> str:
    """Which directory boundary owns this document, per `AGENTS.md`."""
    for prefix, name in BOUNDARIES:
        if path.startswith(prefix):
            return name
    if path.startswith(".claude/"):
        return "harness"
    if "/" not in path:
        return "design-system-of-record"
    return path.split("/", 1)[0]


def service_of(path: str) -> str | None:
    """The service a document belongs to, when it sits inside one."""
    match = re.match(r"services/([a-z0-9-]+)/", path)
    return match.group(1) if match else None


def standing(path: str, text: str, declared: dict[str, str]) -> str:
    """How settled this document says it is.

    Read in the order the repository itself would: the document's own `Status:`
    line, then the standing its service manifest declares, then nothing. A
    document that says nothing reads as `unstated` rather than being guessed at -
    67 of them currently do, and that is a finding rather than a gap to paper.
    """
    match = STATUS_LINE.search(text)
    if match:
        return match.group(1).strip()
    service = service_of(path)
    if service and service in declared:
        return declared[service]
    return UNSTATED


def settled(value: str) -> str:
    """Grade a written standing, or return it unchanged when no grade claims it."""
    upper = value.upper()
    if upper == UNSTATED.upper():
        return UNSTATED
    for grade, tokens in GRADES:
        if any(token in upper for token in tokens):
            return grade
    return value


class Offices:
    """Office and village, read from the tables that already assign them."""

    def __init__(self, root: Path) -> None:
        self.by_service: dict[str, str] = {}
        self.village: dict[str, str] = {}
        offices = root / "contracts" / "capability-offices.json"
        if offices.exists():
            for capability, entry in json.loads(
                    offices.read_text(encoding="utf-8"))["assignments"].items():
                service = capability.split(".", 1)[0]
                self.by_service.setdefault(service, entry["office"])
        villages = root / ".claude" / "epic" / "villages.json"
        if villages.exists():
            for name, entry in json.loads(
                    villages.read_text(encoding="utf-8"))["villages"].items():
                for domain in entry.get("domains", []):
                    self.village[domain] = name

    def office(self, path: str) -> str | None:
        service = service_of(path)
        return self.by_service.get(service) if service else None

    def village_of(self, path: str) -> str | None:
        service = service_of(path)
        return self.village.get(service) if service else None


def service_standings(root: Path) -> dict[str, str]:
    """What each service manifest declares about itself."""
    declared = {}
    for manifest in sorted((root / "services").glob("*/contracts/service.json")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        declared[data["service_id"]] = data["standing"]
    return declared


def facets_for(path: str, text: str, offices: Offices,
               declared: dict[str, str]) -> dict[str, Any]:
    """Every facet of one document, each derived from a record that already exists."""
    raw = standing(path, text, declared)
    return {
        "kind": kind(path),
        "kind_note": kind_note(kind(path)),
        "boundary": boundary(path),
        "standing": raw,
        "settled": settled(raw),
        "office": offices.office(path),
        "village": offices.village_of(path),
        "service": service_of(path),
    }
