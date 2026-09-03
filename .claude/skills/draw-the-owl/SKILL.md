---
name: draw-the-owl
description: >-
  Turn a rough ask into a complete, inspectable attempt early, then redraw that same target from feedback
  without drifting into another project. Use on draw the owl, make the whole thing, stop planning and build
  it, build an end-to-end slice. Not for diagnosis or review, and never past the user's authority.
license: MIT
compatibility: >-
  Any Claude host that can produce and revise the artifact in question. A host that can only describe the work
  cannot draw a complete attempt, which is the whole method.
metadata:
  bdos: true
  version: 1.4.0
  hosts: [claude, codex]
  portability:
    behavior: any
    execution: host
  activation: [explicit]
  control: loop
  role: build
  reach: workspace
  takes: [ask, map, chart, verdict]
  gives: result
  hands_off: [kill-your-darlings, is-it-good, can-it-run-doom]
  calls: [why-what-how]
  reports_to: [read-me-in]
  refuses:
    - a plan or an outline in place of an attempt
    - replacing an adopted result when the feedback was a correction to it
    - literalising the owl when the user wants no owl imagery
    - executing beyond the user's authority because a route looks open
  checks:
    - reads: output
      expect: a complete thing exists to react to, not a description of one
      how: "read: can the user try, run, or mark this pass without anything further being built?"
    - reads: output
      expect: every mark from the last round is visible in the new pass, and what was adopted is unchanged
      how: "read: walk the previous round's marks one by one and point at each in the new pass"
  provenance:
    author: bdo
    origin: hand-written from draw-the-owl; the engine stays in the Owl repo (docs/ROSTER.md 8)
    adopted: 2026-09-01
  currency:
    verified: 2026-09-02
    artifact_digest: sha256:3297ffdb4caca46971c25eca310518dba37f6073c1782934315b759de8c8f4de
    basis:
      - path: FORMAT.md
        digest: sha256:e78cc6562cefadcec726ba830f7f2a5f63adb7edbe6a721e6d5b1006eb5f4462
---

# draw-the-owl

The drawing tutorial: two circles, then "draw the rest of the owl". Everything hard is in the step that
got skipped, so this core does that step first — a complete attempt, made early enough that someone can
inspect it, mark it, and get it redrawn. After that you keep redrawing the same owl once it has earned
recognition, unless the user replaces it or combines it on purpose. The owl is
whatever artifact is seeking someone's attention: a function, a page, a paragraph, a decision. Do not
make the user learn owl words, and do not draw an actual owl unless one was wanted.

## The move

Four handles carry the work. The **target** is the result the ask is trying to obtain, or during open
exploration the field constraining the marks until something earns recognition. The **current** is the
latest accepted or inspectable result, including what must be preserved. A **mark** is feedback, a
constraint, evidence, or a discovered reason to change the current. A **pass** is a complete new attempt
at the authorised scope. Everything else uses ordinary domain words: function, paragraph, screen, test.
Name a part separately only when treating it on its own could change recognition, correctness, authority,
or completion.

There are two ways to begin. **Owl first**, when the artifact and what would make it recognisable are
already visible: bind the placeholder to the real thing and then say "binary agent", not "owl". **Inkblot
first**, when the user wants to make marks and see what emerges: do not force an early target or a
requirements interview, make a complete exploratory artifact inside the available field, offer a few
readings as invitations rather than conclusions, treat attraction, rejection, surprise, and association
as marks, and bind the target only after something earns attention. An inkblot is a pass, not
preparation for one, so it must be substantive enough to react to.

Then the drawing grows in steps. A **shape** is something concrete that can be seen or tried. A **part**
is a shape with a known place in the target. A **feature** is something a part has or does that matters
to recognition or use. The **whole** is enough parts and features working together that the target can be
judged. The rhythm bends: several steps may still be shapes, a feature may open its own cycle, and a
whole at one scale is a shape at the next. Stop counting structure as soon as enough is known to draw the
whole, because a step that only discusses a later step is not progress in the drawing.

Scale the reply to the edit. A tiny correction gets a tiny pass. A substantial pass may show its
construction, its history, its evidence, and how it currently feels.

## Refuses

An outline where an attempt was asked for. Drifting into a different project because ambiguous feedback
was read as a new brief; once the user adopts a result, ambiguous feedback is a mark on that result, and
replacing or combining needs an explicit request. Reading the metaphor literally and producing owl
imagery nobody wanted. Going past what the user actually has authority to change, however open the route
looks.

## Hands off to

kill-your-darlings first when the pass is prose, because cutting comes before judging and a judge should
read what will actually ship. is-it-good next, for marks from someone who did not draw, and directly when
the pass is not prose. can-it-run-doom when the pass works and the question is whether the next load
will need a new part for every request. Uses why-what-how to bind the ask, or to bind the target once an inkblot earns
attention. Reports to read-me-in afterwards, which is an account of the work rather than an exit from
it.

## Check

Ask whether the user could try, run, or mark this pass with nothing further built; a description fails.
Then walk the previous round's marks one at a time and point at each of them in the new pass. Then
confirm what the user adopted is still there.

## Example

Ask: "a status page for the queue." First pass: a real page, one queue, live counts, ugly but complete.
Mark: "numbers are right, I want it per repository." Pass: the same page grouped per repository, with the
colours and layout untouched because silence adopted them. Mark: "actually make it a table." That is an
explicit replacement, so the page becomes a table.

## Experience

Record how many redraws it took and what the first complete attempt got wrong. If the first attempt is
usually close enough, the target was too small for this core and something simpler would have done. If the
redraws pass three, the target moved while you were drawing, and the entry should say who moved it.
