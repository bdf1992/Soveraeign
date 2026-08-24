# 0021 · The semantic cold-start task

Status: `PROPOSED · OWNER RATIFICATION PENDING`

Answers open decision **O8**, and closes seam **S5**.

## Decision

Declare the semantic cold-start task as a **custody round trip under mutation**,
recorded as `FOUND-010` and executable as `scripts/sov_witness.py semantic`.

The witness supplies bytes derived from a seed it chooses, which the corpus has
never held. It ingests them, reads the version back, and compares digests it
computed itself. It then mutates the source on disk and asks the system to read
the source again. Six things must hold: the returned bytes are byte-identical to
the bytes supplied; the version resolves the exact source it came from; an
unchanged source still verifies; a changed source is refused as `SOURCE_CHANGED`
rather than read; custody is unaffected by the mutation; and the refusal is
receipted.

## Why this task and not another

O8 asks what observation completes semantic cold-start beyond schema validity.
The test of a candidate is whether a passing result could be produced by a system
that has the right fields and no competence.

This one cannot be. The verdict is byte equality on data the witness authored
seconds earlier. A schema cannot satisfy it, a fixture cannot satisfy it, and a
receipt saying the right words cannot satisfy it. The witness never reads the
implementation, and never trusts a value the system reports about itself: it
hashes what it supplied and hashes what came back.

It also exercises the requirement that was most exposed. `PROD-I-2` says a source
rereads byte-identical by digest. `services/asset/contracts/service.json` has
always declared a `read-version` operation, and the service had no such method,
so that requirement had positive and defeating fixtures for field presence and
had never been performed on real bytes. Declaring the task found the gap; closing
it is `custody.py`.

## Why this unblocks the specification

`SPEC.md` states its own standing rule: self-authored fixtures establish `BUILT`,
an independent run establishes `WITNESSED`, and the owner's recorded decision
establishes `RATIFIED`. `PROD-I-7` requires `semantic_task_observed`, and no task
existed to observe, so the first execution of `FOUND-007` was refused by the
oracle with exactly that defect - correctly.

That refusal, not owner judgement, was what held `SPEC.md` at `PROPOSED`. O10 was
being asked out of order the entire time.

## What this decision does not do

It does not claim the task is sufficient for semantic competence in general. It
is one watched task whose success a fresh witness can determine independently,
which is what S5 asks for and no more. Further tasks may be declared; this one
does not become the definition of competence by being first.

It does not ratify anything. Running it establishes `BUILT` evidence for the
participant and supplies the observation `PROD-I-7` requires. Owner judgement is
still owner judgement.

## Consequences

- `custody.py` implements `read-version` and `reread_source`, both receipted
  including their refusals, in a new module because `lint.py` carries `core.py`
  as known debt with the instruction to split before adding behavior.
- `FOUND-010` is declared and runs in `scripts/verify.py`, so a regression in
  custody fails the repository gate rather than a conformance review months later.
- `FOUND-007` can be re-run against a clean clone once this lands, and can then
  record `semantic_task_observed` truthfully rather than aspirationally.
- Six checks held in 0.103s on first execution.

## Residuals

- The task covers `PROD-I-2` custody semantics. It does not observe semantic
  competence for authority, attestation, or model portability; those requirements
  still rest on field-presence controls.
- The witness runs repository code. Its independence comes from judging on
  self-computed digests over self-authored bytes, not from a separate
  implementation. A second implementation would be stronger.

## Source and authority

- `OPEN-SEAMS.md` S5 cold-start semantics
- `STATUS.yaml` open decision O8
- `SPEC.md` PROD-I-2, PROD-I-7, the `read_source` transition, and the conformance
  boundary at line 379
- `conformance/founding-scenarios/007-fresh-witness.yaml` and its defeating case
  "schema validity is reported as semantic competence"
- `conformance/observations/FOUND-007-observation.json`, the refused first run
- Bdo's 2026-08-23 direction that the specification must earn its standing rather
  than be granted it
