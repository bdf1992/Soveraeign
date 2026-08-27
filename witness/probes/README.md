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

`run` never judges by exit code. Every probe here exits 0 by design, so a probe
whose every check failed to reach its subject still exits 0 and still emits a
well-formed report; liveness is read out of the report's contents instead.

A probe that declares a reach-failure exception and then catches it without
carrying the reason is reported as debt. One that catches it and discards it
fails, because a probe that cannot reach its subject must not be
indistinguishable from one that did.

This directory is empty on `main`. The probes written on
`docs/witness-debt-sweep` (PR #119) land here.
