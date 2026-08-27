# Witness observation receipts

One JSON receipt per observation, conforming to
`contracts/participant-observation.schema.json` — which is checked, not merely
claimed: `scripts/sovwitness/shape.py` validates every receipt against that
schema before grading it, and additionally refuses an empty `participant_id`,
the field naming who observed. A receipt is the machine-readable half of a
witness record: it carries the exact predicate results for a reader who wants
them rather than the prose. `witness/README.md` owns what a witness record is
and what it may not do; nothing here restates it.

A receipt must also digest the probe it names in `telemetry.probe`. Without
that, `STALE_PROBE` below would be opt-in by the receipt's author, who is the
party the rule constrains.

`python scripts/sov_witness_layer.py records` recomputes every digest a receipt
declares in `observed.observed_state_digests` against the bytes at
`observed.observed_state_addresses`, and `scripts/verify.py` runs it. What that
grading means:

| Verdict | Reading |
| --- | --- |
| `CURRENT` | Every address still holds the bytes the witness digested. |
| `STALE_SUBJECT` | The subject moved, or is gone. Reported as debt, not failed: the receipt observes the commit in `artifact_revision` and never claimed to describe the present. A renamed subject is drift, not a broken receipt. |
| `STALE_PROBE` | An address under `witness/` moved. Failed: the receipt no longer describes the code that produced its results. |
| `INVALID` | The receipt's own shape cannot be graded — the schema rejects it, it digests nothing, or it names the same address twice. Failed: it measures nothing while looking as though it does. |

A receipt that still matches the tree is not thereby correct. Grading says the
evidence is still live; what it earns stays the reader's judgement.

This directory is empty on `main`. The receipts written on
`docs/witness-debt-sweep` (PR #119) land here.
