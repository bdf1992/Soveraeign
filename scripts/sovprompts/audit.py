"""Grade a set of workflow sources against the witness-context rule, in one predicate.

`SDLC.md`, Release gate item 6: an independent evaluator receives the contract, the
claimed invariants and the artifact, and never the builder's plan as its oracle.

This exists because the refusals that enforce that rule used to live in prose. Seven
independent readings defeated the check twenty-eight times, and one of those defeats
reproduced across three candidates *after* it had been named, because what refused it was
a docstring rather than a case. `SDLC.md` gate 3 and `AGENTS.md`, Testing and
verification, both require a defeating case per consequential behaviour; the corpus at
`scripts/tests/fixtures/witness-context-defeats.json` is that, and this is what it runs
against.

One predicate, read in two directions. `violations` returns every way a set of sources
breaks the rule: the live tree must produce none, and every case in the corpus must
produce at least one. A repair that closes a defeat without a corpus entry is a repair
nothing will notice losing.
"""

from __future__ import annotations

from sovprompts.bindings import derives_from_agent_result, roots
from sovprompts.calls import agent_calls, scan_is_stable
from sovprompts.dispatch import dispatches, interpolated, prompt_of, resolved_prompt
from sovprompts.lexer import unreadable
from sovprompts.render import blocks
from sovprompts.scan import masked

WITNESS = "sov-witness"
#: The sentence that demotes a builder's account wherever a prompt splices one in.
LABEL = "artifact and never oracle"
#: The same sentence reversed. A presence rule cannot tell one from the other.
INVERTED = "oracle and never artifact"
#: The bindings carrying the builder's own account in the loop.
ACCOUNT = frozenset({"plan", "built", "orchestrationReview"})
#: Each frame instruction is required inside the block that owns it, because moving one
#: elsewhere left the frame with every graded phrase and none of its meaning.
FRAME_OWNERS = {
    "SUBJECT": ("Pin it before you read anything", "git rev-parse HEAD", "UNATTESTABLE"),
    "SCOPE": ("git status", "git diff"),
    "CHECKS": ("scripts/verify.py",),
    "STATE": ("committed bytes",),
}


def _frame_violations(name: str, source: str) -> list[str]:
    """The loop's own frame: it must render, open on the subject, and demote in order."""
    out: list[str] = []
    parts = blocks(source, "witnessFrame")
    if len(parts) < 6:
        return [f"{name}: witnessFrame renders {len(parts)} block(s); the frame is gone"]
    heads = [block.split(".")[0].strip() for block in parts]
    if heads[0] != "SUBJECT":
        out.append(f"{name}: the frame opens on {heads[0]!r}, not the subject")
    by_head = dict(zip(heads, parts))
    for head, required in FRAME_OWNERS.items():
        if head not in by_head:
            out.append(f"{name}: the frame has no {head} block")
            continue
        for phrase in required:
            if phrase not in by_head[head]:
                out.append(f"{name}: {phrase!r} left the {head} block")
    account = next((i for i, h in enumerate(heads) if h.startswith("THE BUILDER")), None)
    if account is None:
        out.append(f"{name}: the frame no longer carries the builder's account at all")
    else:
        for earlier in ("CONTRACT", "CHECKS"):
            if earlier in heads and heads.index(earlier) > account:
                out.append(f"{name}: {earlier} reaches the evaluator after the account")
    return out


def _dispatch_violations(name: str, source: str) -> list[str]:
    """Every witness dispatch in one file, against the rule it has to satisfy."""
    out: list[str] = []
    for call, kind in agent_calls(source):
        if kind is None:
            out.append(f"{name}: a dispatch declares an agent type this cannot read once, "
                       f"so no rule reaches it: {call.strip()[:70]}")
    for call in dispatches(source, WITNESS):
        prompt = resolved_prompt(source, prompt_of(call))
        code = masked(prompt)
        if "witnessFrame(" in code:
            before = prompt[:prompt.index("witnessFrame(")]
            for expression in interpolated(before):
                leaked = sorted(roots(source, expression, ACCOUNT) & ACCOUNT)
                if leaked:
                    out.append(f"{name}: {leaked} reaches a witness ahead of the frame")
            continue
        if INVERTED in prompt:
            out.append(f"{name}: a witness prompt names the builder's account its oracle")
        spliced = interpolated(prompt)
        if spliced and LABEL not in prompt:
            measured = any(derives_from_agent_result(source, e) for e in spliced)
            out.append(f"{name}: a witness prompt splices {len(spliced)} expression(s) "
                       f"with no label demoting the builder's account"
                       + (" (provenance to an agent result is measurable)" if measured
                          else " (provenance not resolvable, which is why a splice is "
                               "what this requires)"))
    return out


def violations(workflows: dict[str, str]) -> list[str]:
    """Every way this set of workflow sources breaks the witness-context rule.

    `workflows` maps a file name to its source. The live tree must return an empty list;
    every case in the defeats corpus must return a non-empty one. Both directions are
    graded, because a check that cannot fail is not a check and a check that fires on
    correct code is worse than the gap it covers.
    """
    out: list[str] = []
    for name in sorted(workflows):
        source = workflows[name]
        defect = unreadable(source)
        if defect is not None:
            out.append(f"{name}: not readable JavaScript: {defect}")
            continue
        if not scan_is_stable(source):
            out.append(f"{name}: what this file is read to contain depends on whether a "
                       "`/` is division or a regex")
            continue
        if "function witnessFrame(" in masked(source):
            out.extend(_frame_violations(name, source))
        out.extend(_dispatch_violations(name, source))
    return out
