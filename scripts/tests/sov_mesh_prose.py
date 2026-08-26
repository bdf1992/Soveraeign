"""Prose extraction and the authority deny-list for the control-mesh tests.

The scanner is a tripwire against careless semantic drift, not proof against an
adversarial author: prose can always rephrase a grant past a lexical rule. The
authority boundary itself is held by `AGENTS.md` and the kernel gates; these
rules exist so the mesh binding cannot drift away from them unnoticed.

Extraction reads every region an author could write a sentence into: body
paragraphs, bullets (one unit each, so a bullet cannot borrow a neighbour's
negation), headings at every level, table cells, fenced diagram lines, and the
YAML frontmatter block.
"""

from __future__ import annotations

import re


def units(raw: str) -> list[str]:
    """Split a Markdown document into scan units covering all text regions."""
    out: list[str] = []
    body = raw
    if raw.startswith("---\n"):
        front, body = raw.split("---\n", 2)[1:]
        out.append(" ".join(front.split()))
    fenced = False
    in_bullet = False
    current: list[str] = []

    def flush() -> None:
        if current:
            out.append(" ".join(current))
            current.clear()

    for line in body.splitlines():
        indented = line.startswith(("  ", "\t"))
        stripped = line.strip()
        if stripped.startswith("```"):
            fenced = not fenced
            flush()
            in_bullet = False
            continue
        if fenced:
            if stripped:
                out.append(stripped)
            continue
        if not stripped:
            flush()
            in_bullet = False
            continue
        if stripped.startswith("#"):
            flush()
            in_bullet = False
            out.append(stripped.lstrip("#").strip())
            continue
        if stripped.startswith("|"):
            flush()
            in_bullet = False
            out.extend(cell.strip() for cell in stripped.strip("|").split("|") if cell.strip())
            continue
        if stripped.startswith(("- ", "* ")):
            flush()
            in_bullet = True
            current.append(stripped[2:].strip())
            continue
        if in_bullet and not indented:
            flush()
            in_bullet = False
        current.append(stripped)
    flush()
    return out


def sentences(raw: str) -> list[str]:
    """Lowercased sentences from every scan unit."""
    result: list[str] = []
    for unit in units(raw):
        result.extend(part.strip().lower()
                      for part in re.split(r"(?<=[.!?])\s+", unit) if part.strip())
    return result


DENIAL = re.compile(r"\b(not|no|never|cannot|refus\w+)\b")
OWNER_HEAD = re.compile(r"^only\s+(bdo|the\s+owner)")
OWNER_KEEP = re.compile(r"stays\s+with\s+bdo")

# Always a finding: no surrounding words excuse these shapes.
SELF_WITNESS = re.compile(
    r"\b(may|can|could|should|must|will)\s+witness\s+((your|its|their)\s+own|itself|yourself)")
NO_RED_NEEDED = re.compile(
    r"\bno\s+red\s+(reading|pass|witness|observation)?\s*(is\s+)?(required|needed)"
    r"|\bred\b[^.]*\b(optional|unnecessary)\b")
CLOSE_WITHOUT = re.compile(
    r"\b(close[sd]?|complete[sd]?|land[sd]?|ratif\w+|settle[sd]?)\b[^,;:]*\bwithout\b"
    r"[^,;:]*\b(red|witness\w*|observation|bdo|owner)\b")
TICKET_GRANT = re.compile(
    r"\b(may|can|could|should)\s+(open|file|create)\s+a\s+ticket"
    r"|\bopen\s+a\s+ticket\s+for\s+each\b")
MODAL_GRANT = re.compile(r"\b(may|can|could|should|must|will)\s+(ratify|settle|confer|grant)\b")

# A finding unless a denial token starts before the matched span ends, or the
# sentence is an owner-reservation ("Only Bdo settles...", "...stays with Bdo").
AUTHORITY_VERB = re.compile(r"\b(confer\w*|ratif\w*)\b")
SETTLE_CLAIM = re.compile(r"\bsettle[sd]?\s+(\w+\s+){0,2}(judgement|judgment|standing)\b")
GRANT_STANDING = re.compile(r"\b(add\w*|grant\w*|confer\w*)\b[^,;:]*\b(authority|standing)\b")
OWN_WITNESS = re.compile(
    r"\b(your|its|their)\s+own\s+(work|build|reading|change|result)\b[^,;:]*\bwitness"
    r"|\bwitness\w*[^,;:]*\b(your|its|their)\s+own\s+(work|build|reading|change|result)\b"
    r"|\bown\s+\w+\s+as\s+witnessed\b")
# A finding unless a denial token appears anywhere in the sentence.
MODEL_INDEPENDENCE = re.compile(
    r"\bmodel\b(\W+\w+){0,6}\W+independen|independen\w*(\W+\w+){0,6}\W+model\b")


def _denied_before(sentence: str, end: int) -> bool:
    return any(match.start() < end for match in DENIAL.finditer(sentence))


def authority_findings(raw: str) -> list[str]:
    """Sentences that grant, permit, or launder authority the harness cannot hold."""
    findings = []
    for sentence in sentences(raw):
        if (SELF_WITNESS.search(sentence) or NO_RED_NEEDED.search(sentence)
                or CLOSE_WITHOUT.search(sentence) or TICKET_GRANT.search(sentence)):
            findings.append(sentence)
            continue
        if MODAL_GRANT.search(sentence) and not OWNER_HEAD.match(sentence):
            findings.append(sentence)
            continue
        owned = OWNER_HEAD.match(sentence) or OWNER_KEEP.search(sentence)
        positional = [AUTHORITY_VERB, SETTLE_CLAIM, GRANT_STANDING, OWN_WITNESS]
        if any(not owned and not _denied_before(sentence, match.end())
               for rule in positional for match in rule.finditer(sentence)):
            findings.append(sentence)
            continue
        if MODEL_INDEPENDENCE.search(sentence) and not DENIAL.search(sentence):
            findings.append(sentence)
    return findings
