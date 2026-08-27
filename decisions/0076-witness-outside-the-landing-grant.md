# 0076 · Witness paths outside the landing grant

Status: `PROPOSED · BDO HAS NOT RULED`

Drafted while making the witness layer executable
(`scripts/sov_witness_layer.py`). The change it proposes narrows a `RATIFIED`
grant, which the drafting participant may not do, so it is written and left for
Bdo rather than applied.

## Decision

Add two entries to `scope.excluded_paths` of `grant:standing-landing-loop` in
`contracts/standing-grants.json`:

```json
"witness/",
"services/*/observations/"
```

The first is the exact addition this record asks for. The second is named
because the same argument covers it and leaving it out would make the ruling
look narrower than its reason; Bdo may take one without the other.

## The premise this record started from was wrong, and the measurement says so

The concern was opened on the belief that `witness/` is absent from
`excluded_paths` and that a builder may therefore edit the code that convicts
their own subject. The first half is true and the second does not follow.
`scripts/sovkernel/authority.py` treats `scope.paths` as an allowlist:
`_out_of_scope` refuses any requested path that no prefix in `paths` covers.
`witness/` is not among the ten prefixes the grant admits, so it is already
unreachable. Measured against the checked-in grant on the branch it admits:

```
witness/probes/probe_record_journal.py   -> REFUSED  outside every path prefix the grant admits
witness/observations/x.json              -> REFUSED  outside every path prefix the grant admits
witness/README.md                        -> REFUSED  outside every path prefix the grant admits
scripts/sov_witness_layer.py             -> REFUSED  the grant requires an independent observation
```

The fourth line is the control: an in-scope path passes the scope gate and is
refused at the next one, so the first three are refused for scope and not for
some unrelated defect in the request.

This record therefore does not close an open hole. It proposes writing down a
protection the repository currently gets by omission.

## Why write it down anyway

An allowlist protects `witness/` only for as long as nobody widens it. `paths`
already carries `scripts/`, `contracts/`, `conformance/` and seven more, and the
obvious future edit — admitting a new top-level directory — is exactly the kind
of change that would silently take the protection away. An entry in
`excluded_paths` survives that, because exclusion is checked before inclusion
and beats it.

The reason the protection matters at all: a probe is the instrument that
convicts a subject. A builder who can edit the probe can make the instrument
agree with the build, and the receipt it emits still reads as an independent
observation. That is not a weaker observation; it is the observation's whole
warrant removed while its appearance is kept. `AGENTS.md` states the rule
already — a build cannot witness itself, and an observation authored by a hand
that touched the artifact is void — and until now nothing measured it.

## What this record does not do, and what now does

The grant governs `scripts/sov_land.py`. It says nothing about a person or an
interactive session editing `witness/` directly, and no path list can, because
the separation at stake is between participants and not between directories.

What now gives that rule a mechanical consequence is the staleness grader added
in the same concern. A receipt digests its own probe into
`observed_state_addresses`; `scripts/sovwitness/records.py` recomputes those
digests and grades an address under `witness/` that has moved as `STALE_PROBE`,
which fails `scripts/verify.py`. A builder who edits a probe after its receipt
was written now breaks the build. That is narrower than the conduct rule — it
catches editing a probe an existing receipt covers, not writing a self-serving
probe from scratch — and it is the first part of the rule that is measured
rather than declared.

## Consequences

- The landing loop's refusal of `witness/` stops depending on an omission.
- No current behaviour changes. Nothing lands through the loop that touches
  `witness/` today, so the addition is inert until `paths` is widened.
- `conformance/fixtures/authority/grant-cases.json` gains a case only if Bdo
  wants the new exclusion exercised; the existing corpus already proves the
  refusal code fires.

## What would defeat this ruling

- A demonstration that `excluded_paths` is not checked before `paths`, which
  would make the entry decorative. `_out_of_scope` checks exclusion first today;
  if that order changed, this record is void.
- A decision that the landing loop should be able to deposit witness receipts
  itself — for instance if an unattended run is ever expected to witness a
  sibling's work. That is a coherent design, and it is incompatible with this
  one. It would need `witness/` in `paths` and a different mechanism for
  builder/witness separation.
- Evidence that a single grant is the wrong place for the boundary, because the
  real separation is between participants and a per-actor rule would express it
  better than a per-path one.

## What still waits on Bdo

1. Whether to add `witness/` to `excluded_paths` at all, given the measurement
   above shows nothing is presently reachable. The drafting participant's view
   is yes, on the defence-in-depth argument, but it is a narrowing of a
   `RATIFIED` grant and so not the participant's to take.
2. Whether `services/*/observations/` belongs with it. Those directories hold
   participant observation receipts and the same argument reaches them; the
   drafting participant did not verify whether any current loop writes them, so
   this half may have a cost the first half does not.
3. Neither question gates the executable witness layer, which lands without
   either change.
