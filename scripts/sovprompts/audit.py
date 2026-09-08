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

import re

from sovprompts.bindings import derives_from_agent_result
from sovprompts.calls import _agent_names, _writes_by_name, agent_calls, scan_is_stable
from sovprompts.dispatch import dispatches, interpolated, prompt_of, resolved_prompt
from sovprompts.lexer import unreadable
from sovprompts.render import EXPR, Unreadable, _literals, blocks, rendered
from sovprompts.scan import masked

WITNESS = "sov-witness"
#: The sentence that demotes a builder's account wherever a prompt splices one in.
LABEL = "artifact and never oracle"
#: The same sentence reversed. A presence rule cannot tell one from the other.
INVERTED = "oracle and never artifact"
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
    try:
        parts = blocks(source, "witnessFrame")
    except Unreadable as defect:
        # Reported, not raised. An independent reading found this escaping the predicate
        # uncaught on legal JavaScript, so the check errored where its own docstring said
        # it refuses - and an erroring check is not a refusing one.
        return [f"{name}: the frame cannot be read: {defect}"]
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
    said = rendered(source, "witnessFrame")
    if LABEL not in said:
        out.append(f"{name}: the frame no longer demotes the builder's account at all")
    elif EXPR in said and said.index(EXPR) < said.index(LABEL):
        # The frame's own interior, which the dispatch rule cannot see. It grades the text
        # before `witnessFrame(` and then stops, so four rules skipped everything the frame
        # itself says - and the frame is the path the whole claim rests on. Measured on the
        # rendered text: on the candidate this was written against, the builder's declared
        # paths reached the evaluator 1,456 characters before the sentence demoting them.
        # A third reading recorded this and six candidates passed with it open, because no
        # case pinned it.
        out.append(f"{name}: the frame splices a value at {said.index(EXPR)} and demotes it "
                   f"at {said.index(LABEL)}; the account reaches the evaluator first")
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
    try:
        frame = rendered(source, "witnessFrame") if "function witnessFrame(" in masked(source) \
            else None
    except Unreadable:
        # `_frame_violations` already reports why, and reporting it twice reads as two
        # findings where there is one.
        frame = None
    for escape in escaped_agent_references(source):
        out.append(f"{name}: {escape}")
    for call, kind in agent_calls(source):
        if kind is None:
            out.append(f"{name}: a dispatch declares an agent type this cannot read once, "
                       f"so no rule reaches it: {call.strip()[:70]}")
    for call in dispatches(source, WITNESS):
        try:
            written = prompt_of(call)
        except Unreadable as defect:
            # Which argument carries the prompt is structural, and a call shape this
            # reader does not understand is refused rather than sliced at a brace.
            out.append(f"{name}: which argument of a witness dispatch is the prompt "
                       f"cannot be read: {defect}")
            continue
        try:
            # Substituted in place by `resolved_prompt`, so the body is the whole resolved
            # text and its splice positions are the ones the evaluator reads in.
            body = resolved_prompt(source, written)
        except Unreadable as defect:
            # Distinct from the rendering refusal below. Both said "what this prompt
            # delivers cannot be read", and a reading found the consequence: the corpus
            # matches its `expects` by substring, so a case could migrate from one branch
            # to the other and still pass as coverage of the branch it left.
            out.append(f"{name}: what this prompt is assembled from cannot be followed, "
                       f"so the rule cannot reach it: {defect}")
            continue
        try:
            # What the evaluator receives, not the source that builds it. `LABEL in prompt`
            # was a substring test over source while `interpolated` skipped comments, so a
            # demotion sitting in a `//` comment, a dead string or an untaken ternary branch
            # satisfied the rule and reached nobody. That asymmetry covered twenty-one of
            # twenty-two workflows: the rendering grader was aimed at the one file a reading
            # had complained about rather than at the rule. A prompt this cannot render is
            # refused rather than fallen back on.
            delivered = _literals(body)
        except Unreadable as defect:
            out.append(f"{name}: what this prompt delivers cannot be read, so the rule "
                       f"cannot reach it: {defect}")
            continue
        if INVERTED in delivered:
            out.append(f"{name}: a witness prompt names the builder's account its oracle")
        if frame is not None and not delivered.startswith(frame):
            # Identity, not presence. A file that declares a frame declares that its
            # evaluators read that text first. An independent reading left the real frame
            # in place as dead code, put `/* witnessFrame( */` ahead of a second helper so
            # one grader saw a frame and the other did not, and delivered a prompt with no
            # subject pin that told the evaluator to take the builder's scope as given.
            # Every presence rule passed. What this compares is the frame's own rendering
            # against the bytes the dispatch delivers, so there is nowhere ahead of it to
            # put anything.
            out.append(f"{name}: this file declares a witness frame and a dispatch does "
                       "not open on it; what the evaluator reads first is not the frame")
        # Read from the body, so the slots counted in the delivered text and the
        # expressions they correspond to come from the same string. Counting one in
        # the resolved text and the other in the body puts the name of the prompt
        # itself in slot zero and shifts every position by one.
        spliced = interpolated(body)
        if spliced and LABEL in delivered:
            # Position, outside the frame as well as inside it. A prompt may carry the
            # label and still put the builder's account first and name it the oracle, with
            # the demotion in a closing footnote; two independent readings defeated the
            # rule that way. Twenty workflows hand-assemble their prompts, so presence was
            # the only rule reaching them, and presence is not position.
            # Delivered order, and only the builder's account. `_literals` marks every
            # interpolation `<expr>` in the order `interpolated` reports them, so the nth
            # marker before the demotion is the nth spliced expression. Counting markers
            # alone convicts a repository path; asking provenance of the source text
            # ignores the transformation that decides what order the evaluator reads in.
            before = delivered[:delivered.index(LABEL)].count(EXPR)
            for expression in spliced[:before]:
                if derives_from_agent_result(source, expression):
                    out.append(f"{name}: {expression.strip()[:40]!r} is delivered before "
                               "the sentence demoting it")
        if spliced and LABEL not in delivered:
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


def escaped_agent_references(source: str) -> list[str]:
    """Every place `agent` reaches an expression this reader cannot follow into a call.

    The enumerator finds dispatches by name, and nine readings closed nine ways of reaching
    `agent` under another one. The ninth found six more - a computed member, the comma
    operator, an array index, `bind`, a conditional, an object member read back - each a
    dispatch node executes and each returning no violation, because a call never
    recognised cannot be refused. Following one more construction closes one instance and
    leaves the class open, so this refuses the class: an occurrence is accounted for when
    it is called directly, or when it is the whole right-hand side of a binding the
    fixpoint already resolved. Anything else is reported rather than followed.
    """
    code = masked(source)
    out: list[str] = []
    for call in re.finditer(r"\beval\s*\(", code):
        # `eval('agent')(prompt, ...)` dispatches a real witness and reports nothing:
        # `masked` blanks string contents by design, so no name occurrence exists to find.
        # Direct eval sees lexical scope, so this is not host-specific. A workflow has no
        # reason to reach its own bindings by name at runtime, and a reader that cannot
        # see through it refuses it rather than claiming a boundary it does not hold.
        # Every `eval`, not the first. This returned on the first one, discarding every
        # other escape in the file including the ones below; an independent reading found
        # it. One refusal is enough to refuse a file and is not enough to describe it, and
        # a reader that stops at the first finding teaches the next reader to hide behind
        # a decoy.
        line = code[:call.start()].count("\n") + 1
        out.append(f"line {line}: `eval` can reach any binding by name, including `agent`, "
                   "and nothing here can read what it dispatches")
    names = _agent_names(source)
    writes = _writes_by_name(source)
    accounted = {name: {written.strip().rstrip(";").strip() for written in items}
                 for name, items in writes.items()}
    for name in sorted(names):
        for match in re.finditer(rf"\b{re.escape(name)}\b", code):
            after = code[match.end():match.end() + 24].lstrip()
            if after.startswith("(") or after.startswith(".call") or after.startswith(".apply"):
                continue
            statement = code[max(0, match.start() - 80):match.end()]
            target = re.search(r"([A-Za-z_$][\w$]*)\s*[:=]\s*$",
                               statement[:len(statement) - len(name)])
            if target and target.group(1) in names:
                continue
            if re.search(r"\b(?:const|let|var)\s+$", statement[:len(statement) - len(name)]):
                continue
            if any(name == value for values in accounted.values() for value in values) and (
                    re.search(r"[:=]\s*$", statement[:len(statement) - len(name)])):
                continue
            line = code[:match.start()].count("\n") + 1
            out.append(f"line {line}: `{name}` reaches an expression this cannot follow "
                       "into a call, so no rule reaches whatever it dispatches")
    return out
