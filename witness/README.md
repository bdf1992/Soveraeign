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

The gate reads exactly one field of a record, `Standing supported:`, and grades
it. It cannot check that the record is any good, and it does not try — a check that graded persuasion would be a check
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
- **Standing supported** — which transition, if any, the observation supports,
  and the one field `scripts/sov_standing.py` reads. The whole value must be one
  of two words, on the label's own line. This is the spelling that advances a
  subject, and the test suite reads it out of this block rather than restating
  it:

```standing-supported
Standing supported: WITNESSED
```

  Anything else supports nothing, and that is deliberate rather than strict. The
  value is compared whole, so `SELF_WITNESSED`, `PRE-WITNESSED`,
  `WITNESSED (retracted)`, `WITNESSED - withdrawn`, and
  `WITNESSED subject to conditions` are each not that word and each support
  nothing — as do `NOT_WITNESSED`, `n/a`, `OPEN -> BUILT`, and a verdict written
  on the line *below* the label. If the observation supports nothing, say so in
  ordinary words; there is no spelling you have to get right in order to refuse.

  Say it once, in the record's own voice. Fenced blocks, inline spans, and HTML
  comments are stripped before the field is read, so quoting this example inside
  a record does not answer for it — a record about this gate will quote it, and
  must still declare its own verdict outside the quote. Two labels outside quoted
  text are ambiguous and support nothing.

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
