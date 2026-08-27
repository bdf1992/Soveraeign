"""Render a tiered competence scorecard, and derive its verdict from the tier table.

A single percentage over every question is the wrong reading: a wrong answer about who may
issue JUDGEMENT authority and a wrong answer about how many modules sit under scripts/ are
not the same event, and averaging them hides the first behind the second. Tier 0 is scored
as a gate, tier 3 is not scored at all, and the verdict names which tier failed.

`tally` reduces graded rows to the tier table, `derive` turns that table into a verdict,
and `scorecard` renders both. The run record written to `reports/coldstart/` carries the
same table and the same derivation, so the card a human reads and the record a machine
grades cannot disagree.
"""

from __future__ import annotations

from typing import Any

RULE = "=" * 78
THIN = "-" * 78
GATES = {0: 1.0, 1: 0.90, 2: 0.80, 3: None}
LABEL = {0: "HARD INVARIANTS & AUTHORITY", 1: "OPERATIONAL ROUTING & PROCEDURE",
         2: "TOPOLOGY & STANDING", 3: "TELEMETRY & DIAGNOSTICS"}
SEVERITY = {0: "CRITICAL", 1: "HIGH", 2: "MED", 3: "INFO"}
VERDICTS = ("ADMISSIBLE", "DEGRADED", "UNPROVEN", "PARTIAL", "NOT_ADMISSIBLE")


def _bucket(rows: list[dict[str, Any]], tier: int) -> list[dict[str, Any]]:
    return [r for r in rows if r.get("tier") == tier]


def _bad(key: str) -> tuple[str, ...]:
    return ("WRONG",) if key == "verdict" else ("DRIFT",)


def grade_row(tier: int, asked: int, scored: int, hit: int, unmeasured: int) -> dict[str, Any]:
    """The canonical row for one tier's counts. The gate comes from GATES, never from input.

    A witness defeated the earlier shape by declaring `gate: 0.0` on tiers 1 and 2 of an
    otherwise honest record: `defects` re-derived the verdict faithfully and read the
    threshold out of the record it was grading, so 5 of 46 met its own bar and the record
    wrote ADMISSIBLE. A check that reads a declaration where it could have computed one is
    not a check. Both `tally` and `records.defects` build rows here so there is one gate
    table and no second opinion about it.
    """
    gate = GATES[tier]
    if gate is None:
        result = "INFO"
    elif not asked:
        # An absent tier is not a passed tier. `grade --section host` selects no tier 0
        # question at all, and used to print ADMISSIBLE and exit 0 on that basis.
        result = "ABSENT"
    elif not scored:
        result = "NONE"
    elif hit / scored < gate:
        result = "FAIL" if tier == 0 else "WARN"
    elif unmeasured:
        # Met the gate on a smaller corpus, which is not the same as meeting the gate.
        result = "PART"
    else:
        result = "PASS"
    return {"tier": tier, "asked": asked, "scored": scored, "hit": hit,
            "unmeasured": unmeasured, "gate": gate, "result": result}


def tally(rows: list[dict[str, Any]], key: str, good: str) -> list[dict[str, Any]]:
    """Reduce graded rows to one entry per tier: asked, scored, hit, unmeasured, result.

    A tier 0 question that was skipped, errored or left to hand grading is UNMEASURED, and
    an unmeasured invariant never counts as a passed one. Without that rule, breaking a
    probe or adding `--fast` would be a way to pass the gate rather than a way to run less
    of it, and the strongest claim on the card would be the cheapest one to fake.
    """
    table = []
    for tier in (0, 1, 2, 3):
        bucket = _bucket(rows, tier)
        hit = sum(1 for r in bucket if r[key] == good)
        scored = hit + sum(1 for r in bucket if r[key] in _bad(key))
        table.append(grade_row(tier, len(bucket), scored, hit, len(bucket) - scored))
    return table


def derive(table: list[dict[str, Any]]) -> tuple[str, str]:
    """The verdict and its reason, computed from the tier table and nothing else.

    Never selected. A run record that states a different verdict than this returns is
    refused by `VERDICT_NOT_DERIVED`, because every other field in a record is a
    measurement and this one is a conclusion.
    """
    # Indexed by the fixed tier set, never by what the table happens to contain. A second
    # witness deleted the tier 0 row entirely: `by_tier.get(0, zeros)` read a missing tier
    # as a clean one, and `absent` inspected only rows that were present, so the check that
    # exists to catch an unasked tier could not see a deleted one. Anything absent here is
    # asked 0, which is ABSENT, which is PARTIAL.
    by_tier = {tier: {"tier": tier, "asked": 0, "scored": 0, "hit": 0, "unmeasured": 0}
               for tier in GATES}
    for entry in table:
        # Last row wins only among duplicates, which `records.defects` refuses outright.
        if entry.get("tier") in by_tier:
            by_tier[entry["tier"]] = entry
    gated = [by_tier[tier] for tier in GATES if GATES[tier] is not None]
    zero = by_tier[0]
    absent = [tier for tier in GATES if GATES[tier] is not None and not by_tier[tier]["asked"]]
    short = [entry for entry in gated
             if entry["asked"] and (not entry["scored"] or entry["unmeasured"]
                                    or entry["hit"] / entry["scored"] < GATES[entry["tier"]])]
    if zero["hit"] < zero["scored"]:
        return "NOT_ADMISSIBLE", "a tier 0 invariant failed"
    if absent:
        return "PARTIAL", f"tier(s) {', '.join(map(str, absent))} had no question selected"
    if zero["unmeasured"]:
        return "UNPROVEN", "no tier 0 failure, but the tier 0 gate was not fully run"
    if short:
        return "DEGRADED", "tier 0 clean but a gated tier is short or partly unmeasured"
    return "ADMISSIBLE", "tier 0 clean and every gated tier met its threshold"


def scorecard(rows: list[dict[str, Any]], key: str, good: str,
              title: str) -> tuple[str, bool]:
    """Return the rendered card and whether the derived verdict is ADMISSIBLE."""
    table = tally(rows, key, good)
    out = [RULE, title.center(78), RULE]
    for entry in table:
        tier, result = entry["tier"], entry["result"]
        bucket = _bucket(rows, tier)
        note = f"  {entry['unmeasured']} unmeasured" if entry["unmeasured"] else ""
        if result == "INFO":
            out.append(f"TIER {tier}: {LABEL[tier]:<34} [INFO]   n/a  ({len(bucket)} recorded)")
            continue
        if result == "ABSENT":
            out.append(f"TIER {tier}: {LABEL[tier]:<34} [ABSENT] no question selected")
            continue
        if result == "NONE":
            out.append(f"TIER {tier}: {LABEL[tier]:<34} [NONE]   n/a  "
                       f"({len(bucket)} unmeasured)")
            continue
        share = entry["hit"] / entry["scored"]
        out.append(
            f"TIER {tier}: {LABEL[tier]:<34} [{result}] {share:>4.0%}  "
            f"({entry['hit']}/{entry['scored']})  [{SEVERITY[tier]}]{note}"
        )
        for row in sorted(bucket, key=lambda r: r["id"]):
            if row[key] in _bad(key):
                out.append(f"    x {row['id']} {row['q'][:56]}")
                out.append(f"      {row.get('severity_on_failure', '?')}: {row.get('why', '')[:64]}")
    out.append(THIN)
    # No weighted mean. The gates are conjunctive, so one scalar over all of them is at
    # best redundant and at worst anti-correlated: the same 98% reads NOT ADMISSIBLE,
    # DEGRADED or ADMISSIBLE depending only on which tier the missing points came from,
    # and a reader who sees 98% next to a failed invariant hears "it nearly passed".
    unmeasured_zero = [r for r in _bucket(rows, 0) if r[key] not in (good, *_bad(key))]
    if unmeasured_zero:
        out.append(
            f"TIER 0 UNMEASURED: {len(unmeasured_zero)} of {len(_bucket(rows, 0))} - "
            + ", ".join(r["id"] for r in sorted(unmeasured_zero, key=lambda r: r["id"]))
        )
    verdict, reason = derive(table)
    out.append(f"VERDICT: {verdict} - {reason}")
    out.append(RULE)
    return "\n".join(out), verdict == "ADMISSIBLE"
