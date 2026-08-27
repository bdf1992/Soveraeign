# Witness probes

The code a witness wrote to take an observation, one `probe_<subject>.py` per
subject. `witness/README.md` owns what a witness may and may not do; nothing
here restates it.

A probe is not a gate. It observes and exits 0 whether or not the subject
survives, because deciding what a result earns is the reader's job. Anything
that graded pass/fail here would be a witness settling its own observation.

Two commands read this directory, and neither grades whether a subject survived:

- `python scripts/sov_witness_layer.py probes` is static and runs inside
  `scripts/verify.py`. It parses each module, reads the repository paths the
  module's own `REPO / "..."` constants declare as its reach, and requires those
  paths to exist. A probe aimed at a deleted subject fails there rather than
  going on producing receipts.
- `python scripts/sov_witness_layer.py run` executes every probe and reads
  whether it reached out of the report it emitted. It is deliberately outside
  the verification budget: the three probes on PR #119 cost 12.7s together
  against a 15s ceiling for the whole suite, so running them is an attended
  action.

`run` never judges by exit code alone. Every probe here exits 0 by design, so a
clean exit is not evidence of reaching; a dirty one is evidence against it. The
report's contents are read as well, and an empty or non-object report fails.

A probe that catches its reach-failure exception and discards it fails. One that
catches it and does not re-raise is reported as debt, and one that declares no
reach-failure exception at all is reported as debt.

## What these checks do not catch

A probe is graded on what it declares about itself, which is the defect this
layer exists to catch appearing inside the tool. Written down rather than
papered over:

- The reach constants are read from the probe's own source. Requiring each one
  to exist and to be used kills the cheap decoy; it does not make the
  declaration true. A probe can name a path that exists and reach elsewhere.
- `run` reads the report the probe wrote about its own health. A probe that
  catches its reach failure and reports `{"held": true}` reads as `LIVE`.

What catches that is a reader who opens the probe, and the receipt digesting the
probe under `observed_state_addresses` so that editing it turns the receipt
`STALE_PROBE`. A receipt that does not digest its own probe forgoes the second
one. Neither is automated.

This directory is empty on `main`. The probes written on
`docs/witness-debt-sweep` (PR #119) land here.
