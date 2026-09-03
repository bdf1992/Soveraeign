---
name: can-it-run-doom
description: >-
  Judge whether a design generates capabilities from primitives or enumerates them one at a time. Not a
  complexity critic: the count of things is not the defect. Ask what happens when someone wants something
  nobody enumerated - do they compose what is already there, or must the design invent another answer.
  The finding is always a primitive that does not exist, never a thing to cut. Use on can it run doom, can it do X, is this general, is this
  overbuilt, is this a substrate, will this extend, why does every new feature need new code, what is this
  actually built on, before committing to a shape, and on a design that keeps growing without getting
  more capable.
license: MIT
compatibility: >-
  Any Claude host. Needs the design in front of it — a map, a chart, or a built thing — and nothing else.
  It reads and counts; it runs nothing and changes nothing.
metadata:
  bdos: true
  version: 1.1.0
  hosts: [claude, codex]
  portability:
    behavior: any
    execution: any
  activation: [explicit]
  control: one-shot
  role: judge
  reach: none
  takes: [map, chart, result]
  gives: verdict
  hands_off: [walk-and-talk, why-what-how, draw-the-owl]
  reports_to: [read-me-in]
  refuses:
    - recommending that anything be removed, cut, simplified, or rewritten
    - calling a design overbuilt from the number of things it does
    - naming a primitive that does not make two or more existing capabilities instances of one composition
    - manufacturing a primitive rather than returning that nothing is missing and the defect is elsewhere
    - picking a load nobody would ever plausibly ask for, which proves nothing
    - demanding generality from a thing with no second load coming
  checks:
    - reads: output
      expect: >-
        the verdict names one primitive that does not exist and the two or more separate capabilities it
        would make instances of one composition, or says plainly that nothing is missing
      how: "read: take the named primitive and write both capabilities as the same composition of it; if they do not collapse, the primitive is a feature request"
    - reads: output
      expect: the capabilities and the concepts are given as two lists a second reader could recount
      how: "read: recount both lists from the artifact alone and see whether you get the same two numbers"
    - reads: output
      expect: nothing in the verdict recommends removing, cutting, or simplifying anything
      how: "read: search for a recommendation to delete, trim, or rewrite; finding one fails the check"
  provenance:
    author: bdo
    origin: hand-written from Bdo's can-it-run-doom question, 2026-09-02, and the Homer Simpson car
    adopted: 2026-09-02
  currency:
    verified: 2026-09-02
    artifact_digest: sha256:d40530e146175304e0c868b75cdc69c27faa0d3c4940cf5e2441d244f315c489
---

# can-it-run-doom

Doom runs on printers, pregnancy tests and oscilloscopes. It was never ported to any of them on purpose;
they run it because each turned out to have memory, arithmetic and a clock, and those compose into things
nobody designed them for. The Homer Simpson car is the other outcome: every request answered with its own
part, three horns, and a shape that still cannot do the one thing you now want. The car does not fail
because of the horns. Removing them changes nothing. It fails because nothing in it was made to combine.

One claim, and it applies to anything with a design: **a good system enumerates primitives and generates
capabilities.** A thing is wide when what it can do grows faster than what you must understand to use it.
This is not a complaint about complexity — the count of things is not the defect, and a large system with
few primitives is fine. The sharper form of the name is the question to actually ask: when I want
something you did not enumerate, do I compose what you gave me, or do you have to invent another answer?

## The move

1. **Name the thing and the scope it claims.** What it is for, in its own words. The judgement is against
   that scope, not against a scope you would have preferred.
2. **List what it can do.** Every capability a user could name. Count them.
3. **List what a user must hold in their head to use it.** Distinct concepts, not features: the kinds of
   thing, the words that have to be learned, the places state lives. Count them.
4. **Read the slope.** Track how the second number moved as the first one grew. Flat is a substrate: new
   capabilities came out of the parts already there. One-to-one is a catalogue: every capability arrived
   with its own concept, and knowing one tells you nothing about the next.
5. **Pick the load.** One workload outside the stated scope that someone might plausibly want next year.
   It has to be real. An absurd load proves nothing and an adjacent one proves nothing either.
6. **Try to run it, on paper.** Express the load using only the parts that already exist. Do not add
   anything. Write down every point where you had to invent something to continue.
7. **Count the inventions.** Zero means the parts compose and the answer is yes. Each invention is a
   named primitive the design does not have.
8. **Say the finding.** Name the missing primitive and the capabilities it would collapse. A primitive is
   the smallest independently meaningful thing, relation, operator, parameter, boundary, or law whose
   existence would make two or more currently separate capabilities instances of the same composition.
   Write both capabilities out as that composition. If they do not both fall out of it, what you have is
   a feature request wearing a better word, and it does not count.
9. **Or say nothing is missing.** Sometimes the design is fine and the trouble is elsewhere. Say that.
   Inventing a primitive so the verdict has content is the failure this whole move is most prone to.

Asked of a design that is still a map, this is cheap and the answer changes what gets built. Asked of a
built thing it is the same reading and a more expensive answer, which is an argument for asking early.

## Refuses

Recommending that anything be removed. The finding is a floor that is missing, never a thing to cut, and
a design that loses features is still the same design. Calling something overbuilt because it does a lot;
count is not the defect and never was. Naming a primitive that collapses nothing, which is how
this becomes a licence to redesign whatever is in front of you. Manufacturing a primitive rather than
returning that nothing is missing; because this may not subtract, it can express any defect at all as
something that ought to exist, and that is the failure to watch for. Choosing a load nobody would ask for so
the verdict comes out no. Demanding generality from a script that runs once and gets deleted, because
there is no second load and no floor is owed.

## Hands off to

walk-and-talk when the missing primitive is real and where it belongs is now an open question. why-what-how
when the reading is that the scope was never bound, and the design grew a part per request because nobody
had said what done was. draw-the-owl when the primitive is clear enough to attempt. Reports to read-me-in
when someone who was not here has to hear what the design cannot do.

## Check

Read the verdict back. It must name one primitive that does not exist, and both capabilities must be
writable as the same composition of it — or it must say plainly that nothing is missing. The two counts must be lists a second reader can recount
from the artifact and get the same numbers. And nothing in it may recommend removing, cutting, or
simplifying; if that sentence is there, this ran as taste rather than as a count.

## Example

A reporting tool with fourteen report types, each with its own page and its own code. Load: "give me the
same numbers weekly instead of monthly." Tried in the existing parts: every report has its window
hardcoded, so the only way through is a fifteenth report type, then a sixteenth for daily. Counts:
fourteen capabilities, fourteen concepts, one-to-one, and the slope has been one-to-one since the third
report. Missing primitive: a window, separate from a report, that any report is evaluated over. It
absorbs the daily, weekly and monthly variants of all fourteen. Nothing is deleted and the fourteen keep
working; they become fourteen reports and one window instead of forty-two report types.

## Experience

Record which load was chosen and whether it was the one that mattered. If the load keeps being one the
design handles easily, the loads are being picked to pass and the reading is worthless. If the same
missing primitive is named across three different subjects, that primitive belongs in whatever those
three share, and the entry should say what that is. If verdicts keep coming back "nothing is missing" on
things that later got stuck, step 5 is choosing loads too close to the stated scope.
