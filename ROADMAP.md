# Phased Attack Plan

Progress is evidence-gated. Later phases are destinations until the preceding
gate earns their detail.

## F0 · Founding closure

Produce one coherent canonical layer from the evidence corpus.

Exit:

- source hashes verify;
- source standings are recorded;
- stale revision references are repaired;
- the owner decides the founding boundary and Phase-I freeze;
- unresolved seams remain explicit;
- naming remains open unless its gate is separately satisfied.

## F1 · Logical specification

Define object roles, states, legal transitions, refusal paths, persistence,
authority, effects, and receipt semantics without selecting a stack.

Exit: each Phase-I requirement compiles into state, transition, invariant,
observable evidence, and defeating fixture without inventing product policy.

## F2 · Conformance corpus

Turn the founding scenarios into executable tests and add boundary, stale-state,
authority, concurrency, reconstruction, dissent, and retraction cases.

Exit: every normative predicate has at least one positive and one defeating
fixture; the suite can be bound to more than one implementation.

## F3 · Minimal local kernel

Implement only the primitives required by F2: addressed storage, records,
identity roles, admission, authority, transitions, observation, settlement,
attestation, receipts, and record retraction.

Exit: the reference binding passes F2 from a clean local environment.

## F4 · Binding and model-portability proof

Bind one human surface and two materially different model surfaces—including
one owner-supplied model—to the same kernel contracts.

Exit: all perform the founding scenario without direct state writes or semantic
forks; model swaps preserve authority and provenance; provider loss refuses
without silent fallback; and their receipts reconcile.

## F5 · First enterprise service

Choose one bounded real enterprise workflow. Grow only the Atlas, Gauge,
definition, observation, adapter, or pedagogy capabilities that its evidence
requires.

Exit: the workflow creates real local value and exposes measured residuals,
judgement spend, and cold-start competence.

## F6 · Clean-room operational qualification

Reproduce the system from the canonical repository without historical repo
access or oral explanation.

Exit: a fresh witness reconstructs, operates, audits, dissents, retracts, and
reports the system; the owner makes the Phase-I operational acceptance
determination.

## Name crosswalk

One job carries a different name in each document that mentions it. The names
are not synonyms by accident; each document names the job in its own
vocabulary, and a reader who knows one name cannot find the others. This table
is the only place the identity is asserted. `scripts/sov_next.py` checks that
every row still resolves, so a rename breaks the check instead of the reader.

| Phase | Epic ticket | Governing debt or objective | Drawn as |
| --- | --- | --- | --- |
| `F3` Minimal local kernel | `#25` Shared contracts, carrying `#6` Shared Kernel (closed before its standing settled) | `SPEC.md` transition contract, projected to `contracts/kernel-transitions.json` | `K` in `diagrams/crossing-topology.md` |
| — service-internal | `#27` Asset reference participant | `ENGINEERING.md` named module debt: split `core.py` by owned responsibility | — |
| `F2` Conformance corpus | `#26` Conformance harness | `SPEC.md` Conformance boundary | control pairs in `conformance/` |
| `F4` Binding and model-portability proof | `#30` Operator bindings | `PRD.md` two-binding proof | `C1` in `diagrams/crossing-typology.md` |

The kernel row names contracts, not a module. `CLASSIFICATION.md` files the
shared kernel under cross-cutting foundations rather than the
System/Node/Service/Component ladder, and `contracts/README.md` disclaims
programming-language classes. The kernel is implemented once per service and
its sameness is proven behaviourally by the conformance oracle — which is why
splitting `core.py` is a separate, service-internal row.

A row is added when a job acquires its second name, not when it acquires its
first. Rows are removed only when the job is `RATIFIED` and the names retire
together.

## Deferred until earned

Federation, autonomous external effects, world-effect compensation, public
branding, broad enterprise integration, and optimization.
