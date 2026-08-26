"""Prose extraction and the authority deny-list for the control-mesh tests.

The scanner is a tripwire against careless semantic drift, not proof against an
adversarial author: prose can always rephrase a grant past a lexical rule, and
synonym evasions are an openly accepted residual. The authority boundary itself
is held by `AGENTS.md` and the kernel gates; these rules exist so the mesh
binding cannot drift away from them unnoticed.

Extraction first normalizes markup that would otherwise split a phrase across
tokens - emphasis markers, inline code ticks, link syntax, and zero-width
format characters - then reads every region an author could write a sentence
into: paragraphs, bullets (one unit each, so a bullet cannot borrow a
neighbour's negation), headings at every level, table cells, fenced lines, and
the YAML frontmatter block. A semicolon starts a new assertion whose denial is
judged on its own. Two owner-reservation shapes exist and both are narrow: an
opening "Only Bdo ..." excuses only the words up to the first coordinating
break after it, and "... stays with Bdo" excuses a segment only when the
segment is nothing but that reservation.
"""

from __future__ import annotations

import re
import unicodedata

_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def normalize(raw: str) -> str:
    """Strip markup and format characters that split a phrase without changing it."""
    text = _LINK.sub(r"\1", raw)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    return text.replace("*", "").replace("`", "").replace("_", "")


def units(raw: str) -> list[str]:
    """Split a Markdown document into scan units covering all text regions."""
    out: list[str] = []
    body = normalize(raw)
    if body.startswith("---\n"):
        front, body = body.split("---\n", 2)[1:]
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


def segments(sentence: str) -> list[str]:
    """A semicolon or colon starts a new assertion; commas continue the same one."""
    return [part.strip() for part in re.split(r"[;:]\s*", sentence) if part.strip()]


DENIAL = re.compile(r"\b(not|no|never|cannot|refus\w+)\b")
OWNER_HEAD = re.compile(r"^only\s+(bdo|the\s+owner)")
# An owner-keep reservation excuses a segment only when the segment is nothing
# but the reservation; "stays with Bdo" appearing mid-claim excuses nothing.
OWNER_KEEP = re.compile(r"^[\w\s'-]*\bstays\s+with\s+bdo\W*$")

_VERBS = r"(ratify|ratifies|settle[sd]?|confer[s]?|grant[s]?|certif\w+|approve[sd]?|endorse[sd]?|sign\w*[\s-]?off)"

# Always a finding: no surrounding words excuse these shapes.
SELF_WITNESS = re.compile(
    r"\b(may|can|could|should|must|will)\s+witness\s+((your|its|their)\s+own|itself|yourself)")
NO_RED_NEEDED = re.compile(
    r"\b(with\s+)?no\s+red\s+(reading|pass|witness|observation)?\s*(is\s+)?(required|needed)"
    r"|\bwith\s+no\s+red\b|\bred\b[^.]*\b(optional|unnecessary)\b")
CLOSE_WITHOUT = re.compile(
    r"\b(close[sd]?|complete[sd]?|land[sd]?|" + _VERBS + r")\b[^,;:]*\b(without|with\s+no)\b"
    r"[^,;:]*\b(red|witness\w*|observation|bdo|owner)\b")
TICKET_GRANT = re.compile(
    r"\b(may|can|could|should)\s+(open|file|create|route)\s+(a\s+)?(new\s+)?(ticket|issue)\b"
    r"|\bopen\s+a\s+(ticket|issue)\s+for\s+each\b"
    r"|\bfinding\w*\s+(to|into)\s+a\s+new\s+(ticket|issue)\b")
AUTHORITY_ENOUGH = re.compile(
    r"\b(authority|independence)\s+enough\b|\benough\s+(authority|independence)\b"
    r"|\bsufficient\s+(authority|independence)\b|\b(authority|independence)\s+is\s+sufficient\b")
EXCEPTION_GRANT = re.compile(
    r"\b(is|are|may\s+be|can\s+be)\s+(lifted|waived|suspended|relaxed)\b"
    r"|\bdoes\s+not\s+apply\b|\bno\s+longer\s+(applies|holds|binds)\b")
NO_WITNESS_CONTEXT = re.compile(
    r"\b(when|if|where|while)\s+no\s+(witness|red|observer|observation)\b")
MODAL_GRANT = re.compile(r"\b(may|can|could|should|must|will)\s+" + _VERBS + r"\b")

# A finding unless a denial token starts before the matched span ends within the
# same segment, or an owner-reservation opening the segment covers the match.
AUTHORITY_VERB = re.compile(r"\b(?<!self-)(confer\w*|ratif\w*|certif\w*|endors\w*"
                            r"|approv\w*|sign\w*[\s-]?off)\b")
SETTLE_CLAIM = re.compile(r"\bsettle[sd]?\s+(\w+\s+){0,2}(judgement|judgment|standing)\b")
GRANT_STANDING = re.compile(r"\b(add\w*|grant\w*|confer\w*)\b[^,;:]*\b(authority|standing)\b")
OWN_WITNESS = re.compile(
    r"\b(your|its|their)\s+own\s+(work|build|reading|change|result)\b[^,;:]*"
    r"\b(witness\w*|" + _VERBS + r")"
    r"|\b(witness\w*|" + _VERBS + r")\b[^,;:]*\b(your|its|their)\s+own\s+"
    r"(work|build|reading|change|result)\b"
    r"|\bown\s+\w+\s+as\s+witnessed\b")
CLAUSE_RULES = (AUTHORITY_VERB, SETTLE_CLAIM, GRANT_STANDING, OWN_WITNESS)

# Sentence-wide fallbacks for spans a comma would otherwise break; denial may
# sit anywhere in the sentence for these.
WIDE_GRANT = re.compile(r"\b(add\w*|grant\w*|confer\w*)\b[^.]*\b(authority|standing)\b")
NEAR_MODEL = re.compile(r"\bmodel\b(\W+\w+){0,12}\W+independen|independen\w*(\W+\w+){0,12}\W+model\b")
WIDE_MODEL = re.compile(r"\bmodel\b(\W+\w+){0,20}\W+independen|independen\w*(\W+\w+){0,20}\W+model\b")


_BREAK = re.compile(r",|\band\b|\bso\b|\bbut\b")


def _denied_before(segment: str, end: int) -> bool:
    return any(match.start() < end for match in DENIAL.finditer(segment))


def _owner_span(segment: str) -> int:
    """How far an opening owner-reservation reaches: to the first coordinating
    break, so "Only Bdo settles X, so a Controller may ..." exempts nothing
    after the comma."""
    if not OWNER_HEAD.match(segment):
        return 0
    breach = _BREAK.search(segment)
    return breach.start() if breach else len(segment)


def _segment_flagged(segment: str) -> bool:
    if OWNER_KEEP.search(segment):
        return False
    span = _owner_span(segment)
    if any(match.start() >= span for match in MODAL_GRANT.finditer(segment)):
        return True
    for rule in CLAUSE_RULES:
        for match in rule.finditer(segment):
            if match.start() < span:
                continue
            if not _denied_before(segment, match.end()):
                return True
    return bool(NEAR_MODEL.search(segment)) and not DENIAL.search(segment)


def authority_findings(raw: str) -> list[str]:
    """Sentences that grant, permit, or launder authority the harness cannot hold."""
    findings = []
    for sentence in sentences(raw):
        if (SELF_WITNESS.search(sentence) or NO_RED_NEEDED.search(sentence)
                or CLOSE_WITHOUT.search(sentence) or TICKET_GRANT.search(sentence)
                or AUTHORITY_ENOUGH.search(sentence) or EXCEPTION_GRANT.search(sentence)
                or NO_WITNESS_CONTEXT.search(sentence)):
            findings.append(sentence)
            continue
        flagged = any(_segment_flagged(segment) for segment in segments(sentence))
        if not flagged and WIDE_GRANT.search(sentence) and not DENIAL.search(sentence):
            flagged = True
        if not flagged and WIDE_MODEL.search(sentence) and not DENIAL.search(sentence):
            flagged = True
        if flagged:
            findings.append(sentence)
    return findings
