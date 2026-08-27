# Witness records

A witness record is an observation of an artifact made by something that did not
build it. `AGENTS.md` fixes the lifecycle `OPEN -> BUILT -> WITNESSED ->
RATIFIED` and states that a build report cannot witness itself; this directory is
where the middle step is deposited, and `scripts/sov_standing.py` refuses a
standing claim that has no record here.

## Naming

One file per subject, named for the `*_status` field it supports with
underscores replaced by hyphens:

| Status field | Record |
| --- | --- |
| `asset_service_status` | `witness/asset-service.md` |
| `engineering_framework_status` | `witness/engineering-framework.md` |
| `sov_operating_agent_status` | `witness/sov-operating-agent.md` |

The filename is what binds a record to a subject, so a record for one subject
cannot satisfy a claim about another. That is deliberate and it is tested. It is
also all the filename proves: nothing checks that the text inside is about the
subject the name claims, and a reader should not read the name as evidence of
that.

## Receipts and probes

Two subdirectories hold the machine-readable half of the same work.

- `witness/observations/` holds one JSON receipt per observation, conforming to
  `contracts/participant-observation.schema.json`. A receipt is addressed to a
  reader who wants the exact predicate results rather than the prose.
- `witness/probes/` holds the code a witness wrote to take an observation. A
  probe belongs to the witness, never to the subject: it reaches the subject
  only through a declared surface, and a subject's own test suite is not one.

Neither directory is read by `scripts/sov_standing.py`, which reads `witness/*.md`
and nothing else. A receipt without a record supports no claim.

## What a record must carry

The gate reads exactly one field of a record, from one declared position, and
grades it. It cannot check that the record is any good, and it does not try — a check that graded persuasion would be a check
that ratifies, which nothing here may do. These are the contents a reader needs
in order to do that grading themselves:

- **Verdict** — one of `RATIFIABLE`, `RATIFIABLE-WITH-CONDITIONS`, `NOT-YET`.
- **The commit witnessed.** Not "the working tree". Several sessions write this
  tree at once and files change mid-read; a record that does not name a commit
  is an observation of something that no longer exists.
- **Findings**, each with a severity, an exact path and line, and the concrete
  consequence if the artifact were ratified as-is.
- **Verified** — the commands actually run, with their real exit codes and
  output. Not a summary of them.
- **Conditions** — if the verdict carries conditions, the exact changes that
  would discharge each one.
- **Uncovered** — what the witness did not examine, stated plainly. A record
  that claims total coverage is not usable, because a reader cannot calibrate it.
- **Standing supported** — which transition, if any, the observation supports.
  Say it in the prose, for a reader. Then declare it once, for the gate, in a
  block that is the **first thing in the file** after the heading:

```witness
standing_supported  WITNESSED
```

  Close the block, put nothing but `name  value` field lines inside it, keep it
  to a handful, and let the title heading be the only thing above it. Those are
  bounds rather than style: a block left unclosed once ran on to a quoted example
  far below and declared its value, and a second heading above the block once let
  an example declare in place of the record. A block that breaks any of them
  declares nothing, which is the right answer for a malformed declaration.

  That position is the whole contract, and it is what makes the rest of the
  record free. `scripts/sov_standing.py` reads this block and stops; it never
  searches the document. So a record may quote anything, at any nesting depth,
  fenced or unfenced, terminated or not, without changing what it declares —
  which matters, because the record most likely to quote this page is a record
  about this gate. Earlier versions stripped what looked like quotation and
  searched the rest, and four quotation forms walked past them.

  The whole value must be one word. `WITNESSED` advances a subject; anything
  else supports nothing, including `SELF_WITNESSED`, `PRE-WITNESSED`,
  `WITNESSED*`, `WITNESSED (retracted)`, and `WITNESSED subject to conditions`.
  If the observation supports nothing, write `none` — or omit the block, which
  means the same thing. There is no spelling you have to get right in order to
  refuse; the strictness is entirely on the side that advances standing.

  A record may not declare `RATIFIED`. It carries a subject as far as WITNESSED;
  the owner settles the rest, and the gate names that over-reach rather than
  quietly ignoring it.

## What a witness may not do

A witness may not edit, fix, stage, or commit the thing it examines; an
observation authored by a hand that touched the artifact is void. It may not
ratify — only Bdo ratifies, and a record here supports a transition at most as
far as `BUILT -> WITNESSED`.

A record is evidence, not a settlement. Depositing one does not advance
standing; it makes advancing standing *possible*, and the owner still decides.

## Producing one

`.claude/workflows/sov-witness.js` runs an adversarial pass over a named subject
and returns the record content. The invoking session writes it here, the same
way domain workflows return reports that the controller writes to `reports/`.

The pass is adversarial by construction: every witness is instructed to find
reasons the artifact should **not** advance, and a witness that returns
"looks correct" without having genuinely attacked the artifact is discarded
rather than filed.
