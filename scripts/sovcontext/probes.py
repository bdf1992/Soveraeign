"""The facts this repository states in more than one place.

`AGENTS.md` forbids duplicating a rule in another file as a competing authority,
and the governance skill names "one fact one producer" as its own trigger. Nothing
measured whether either held. Each probe below names one fact, the document that
owns it, and a pattern that finds a restatement of it.

A probe reports producers, not correctness. A restatement may be a legitimate
citation; what the count establishes is how many files a reader has to reconcile
before it knows what the rule is. The owning document is declared here so a
restatement can be distinguished from the statement.
"""

from __future__ import annotations

# fact_id, owning document, human name, regex alternation matching a statement of it
PROBES: tuple[tuple[str, str, str, str], ...] = (
    ("verify-command", "AGENTS.md", "python scripts/verify.py is the required check",
     r"scripts/verify\.py"),
    ("standing-lifecycle", "AGENTS.md", "OPEN -> BUILT -> WITNESSED -> RATIFIED",
     r"OPEN -> BUILT|OPEN → BUILT|BUILT -> WITNESSED|BUILT → WITNESSED"),
    ("effect-classes", "SPEC.md", "RECORD_LOCAL / RESOURCE_CONSUMPTION / EXTERNAL_WORLD",
     r"RECORD_LOCAL"),
    ("acceptance-not-approval", "AGENTS.md", "the owner gate is acceptance, not permission",
     r"acceptance, not approval|acceptance over|not permission to begin|PREAPPROVAL_REQUESTED"),
    ("no-self-witness", "AGENTS.md", "a build cannot witness itself",
     r"cannot witness itself|not witness its own|witness its own work"),
    ("live-grant", "AGENTS.md", "consequential transitions need a typed scoped live grant",
     r"typed, scoped, live|typed live grant|live grant"),
    ("one-concern", "AGENTS.md", "one session, one concern",
     r"one session, one concern|one bounded concern"),
    ("blocked-is-proven", "AGENTS.md", "BLOCKED is a claim that must be proven",
     r"reachable_alternative|BLOCKED is a claim"),
    ("module-ceiling", "ENGINEERING.md", "modules stay below 300 lines",
     r"below 300|300 lines|300-line"),
    ("phase-i-closed", "STATUS.yaml", "Phase I is terminal CLOSED_INCOMPLETE",
     r"CLOSED_INCOMPLETE"),
    ("judgement-is-bdo", "AGENTS.md", "only the root seat ratifies judgement",
     r"only Bdo|Bdo ratifies|judgement authority"),
    ("record-is-append", "SYSTEM.md", "the Record is append-preserving",
     r"append-preserving"),
)
