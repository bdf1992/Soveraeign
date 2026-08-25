# Ratification docket — 2026-08-23

Requested by Bdo, 2026-08-23: "Ratify everything that agrees with the PRD and
Spec as long as it meets the AI Native and Product/Anchoring parts, otherwise a
specific leading question with recommendations."

This is a report, not policy (`CLAUDE.md`, Where to look first). It records a
screen; it ratifies nothing. Ratification is Bdo's (`AGENTS.md`, Authority), and
`OPEN-SEAMS.md` S12 says the surface it arrives through is itself unsettled.

Screened by the interactive Claude Code session against the working tree at
`feat/federation-harness-and-hardening`, 19 uncommitted paths.

Checks run: `python scripts/verify.py` PASS (198 tests, 1.097 s wall against a
3 s budget); `python scripts/lint.py` PASS (307 text files, 70 modules, one
named debt); `python conformance/run.py` PASS (20 cases, 0 coverage gaps, every
`-DEF` case defeats as declared).

## The instruction has three legs; two cannot be computed today

Bdo's condition is a conjunction. Screening it means evaluating each leg.

**Leg 1 — agrees with PRD and SPEC.** Computable from the artifact. Results per
item below. Most records pass this leg.

**Leg 2 — meets the AI-Native part.** `AI-NATIVE.md` states its unit of
evaluation is "a surface performing a named operation". So this leg applies to
the Asset Service, the local model adapter, the lineage corpus, the conformance
oracle and the coordination registrar — and does not apply at all to a
vocabulary or boundary record such as `CLASSIFICATION.md` or the Proofing
charter, which perform no operation. For every surface it does apply to, the
`SOVERAEIGN_QUALIFIED` bar requires `independent_observation: PASS`, and nothing
here has been witnessed: every `*_status` field in `STATUS.yaml` reads
`NOT_WITNESSED` or `PROPOSED`. The bar also requires `earn_it`, which
`AI-NATIVE.md` defines as "a human judgement with an attributable reviewer" and
whose `OPEN` value "is not a favorable result". Both missing inputs belong to
Bdo and to an independent agent, not to the artifact. **Leg 2 evaluates to NOT
MET for every surface in the repository.**

**Leg 3 — meets the Product/Anchoring part.** Not evaluable from this checkout.
`ANCHOR.md` A1–A10, `SUBSTRATE.md`, `PRODUCT(1).md` and `PRD-PRODUCT(1).md` are
cited 31 times across nine governing files and six decision records. None exist
in the working tree, and `git log --all --diff-filter=A -- 'lineage/*'` returns
nothing: they have never been committed. That is `PUBLICATION.md` operating as
designed — `lineage/` and "immutable historical evidence documents" stay
unpublished until Bdo approves. But the same document adds that a checkout
"must never claim a digest verification it could not perform", and
`decisions/0003` rules that "a missing cited dependency makes the dependent
claim unattestable". `lineage/EXTERNAL-SOURCES.lock`, which 0003 names as the
digest register for that packet, does not exist either. The new
`lineage/SOURCES.lock` registers 159 sources — 65 commits, 51 issues, 18 pull
requests, 25 session files — and none of them is the founding packet.

So the conjunction's "otherwise" branch fires for every item on the docket. What
separates the items is *which* leg fails, because that names the unblock.

## Docket

`L1` = agrees with PRD/SPEC. `L2` = AI-Native, `n/a` where the record performs
no operation. `L3` = anchoring citations verifiable from this checkout.

### A · Clean on every computable leg — waiting only on Bdo's word

No implementation to witness, no anchoring citation, no conflict found. These
are ratifiable as soon as the Q1 mechanism question is answered.

| Record | Gate | L1 | L2 | L3 | Recommendation |
| --- | --- | --- | --- | --- | --- |
| `0023` transition-local gates | none, owner-directed | PASS | n/a | n/a | Ratify. Wording matches `AGENTS.md` Authority; you already directed it. |
| `0024` unblock ticket kind | none, owner-directed | PASS | n/a | n/a | Ratify. Supplies the `BLOCKED`-must-be-proven path `AGENTS.md` requires and nothing else claims. |
| `0026` federation harness | unregistered | PASS | n/a | n/a | Ratify the pattern — roles stable, domains in skills. Hold the "are executable workflows admissible before their defeating fixtures exist" question; that one is Leg 2 in disguise. |
| `0018` verification-engagement kind | O19 | PASS | n/a | n/a | Ratify. Refusing construction identity on a verification ticket is `SDLC.md`'s no-both-hands-of-a-dyad rule made checkable. |
| `0021` Asset Projection Service boundary | O21 | PASS | n/a | n/a | Ratify the boundary and the name, and rule S14 in the same stroke — who keeps `rebuild-projection` for the Asset Service's own two tables. Otherwise it reopens immediately. |

### B · Fails Leg 2 only — needs a witness, not a ruling

Built, self-tested, conformant to PRD and SPEC on inspection. Each is blocked on
the same missing thing: an independent observation. `AGENTS.md` forbids a build
from witnessing itself, and the interactive session that dispatched these runs
cannot supply it either.

| Surface | Gate | L1 | Missing |
| --- | --- | --- | --- |
| Asset Service | none | PASS | witness pass; Bdo's `earn_it` |
| Local model adapter `adapters/ollama/` (`0027`) | O12 | PASS | witness pass; Bdo's `earn_it` |
| Lineage corpus (`0028`) | `lineage.ratify_corpus` | PASS | witness pass — W1–W4 in 0028 declare themselves non-independent |
| Conformance oracle | none | PASS | witness pass |
| Coordination registrar (`0016`) | O16 | PASS | witness pass; authorisation of the outward-facing steps |
| Lessons loop (`0029`) | `lessons.ratify_loop` | PASS | 0028 witnessed first — its evidence addresses resolve there |

`0027` is the strongest object in this group: two materially different local
bindings (`qwen3:4b` and `gpt-oss:20b`), fourteen defeating fixtures, and a
concrete refusal (`DATA_BOUNDARY_REFUSED`) at the real `gpt-oss:20b` /
`gpt-oss:20b-cloud` ambiguity where a binding could claim local custody while
input left the node. It still does not execute `invoke_model`, so PROD-I-9's
"two model bindings attempt the same named operation" is declared, not
performed.

### C · Fails Leg 3 — the founding spine

These are the records whose ratification would close F0 and F1. They are also
the records that cite evidence this checkout cannot verify.

| Record | Gate | Cites |
| --- | --- | --- |
| `0001` founding boundary | none | `ANCHOR.md` A1–A10 |
| `0003` evidence boundary | none | `lineage/evidence/core/`, `EXTERNAL-SOURCES.lock` (absent) |
| `0007` asset service boundary | none | `ANCHOR.md` A1, A8 |
| `0008` classification contract | O9 | `ANCHOR.md` A1, A8 |
| `0009` Phase-I logical spec | O10, `roadmap.close_f1` | SPEC traceability table: SUBSTRATE R1–R6, ANCHOR A2–A10 |
| `0010` proofing service boundary | O11 | `ANCHOR.md` |
| `0011` local personal BYOM | O12 | `ANCHOR.md` A3, A4, A8, A10 |

Ratifying these today ratifies claims whose ground the artifact cannot resolve.
That is exactly what `decisions/0003` calls unattestable and what `AI-NATIVE.md`
scores as a provenance failure.

### D · Carries a conflict that must be ruled before agreement is askable

| Item | Conflict |
| --- | --- |
| `0025` verification channels (O20) | `SDLC.md` `GREEN` (a derived go-state) and the `green` channel (contact with the world) are two meanings of one word. O20 already names this; screening cannot resolve it. |
| `AI-NATIVE.md` Soveraeign bar (S13) | The document requires `FULL` on reachability, commitment, provenance and the effect envelope, omits retraction from that list, then calls it "the all-`FULL` Soveraeign bar". Leg 2 of this instruction *is* that bar, so the ambiguity is load-bearing. |
| `0022` story ticket kind (O22) | Sound on its own. Its second gate is `classification.ratify`, which is O9, which sits in group C. |
| `0016` coordination registrar (O16) | Ratifying it authorises branch protection, label synchronisation and project field writes — `EXTERNAL_WORLD` effects, against `protected_boundaries: no_external_effects_in_phase_i`. |

## AI-Native assessment records

Filled in the `AI-NATIVE.md` required shape for the two surfaces most likely to
be ratified next. Both are `assessment_state: OPEN` because `earn_it` has no
attributed reviewer. Producing these is verification-typed work; the judgement
inside them is not supplied.

```yaml
surface: services/asset
operation: capture, derive, relate, authorize, verify, retract an asset
artifact_revision: feat/federation-harness-and-hardening (uncommitted tree)
model_and_host: Claude Opus 5, Claude Code CLI, Windows 11
scores:
  reachability: FULL        # CLI and contracts/service.json declare every operation
  commitment: PARTIAL       # standing recorded; typed ratification path not exercised
  provenance: PARTIAL       # source, digest, derivation resolve; reader configuration partial
  retraction: PARTIAL       # record-local counteraction exists; effect-class handling declared, not proven
earn_it:
  value: OPEN
  reviewer: unassigned - Bdo
assessment_state: OPEN
minimum_verdict: underivable while earn_it is OPEN
soveraeign_checks:
  same_world_parity: UNATTESTABLE      # no human binding exists
  typed_authority: PASS
  independent_observation: UNATTESTABLE
  receipt_completeness: PASS
  effect_honesty: PASS
  cold_start_competence: UNATTESTABLE
  two_binding_proof: FAIL              # zero of three required bindings execute
  local_sovereignty: PASS
  model_substitutability: UNATTESTABLE # invoke_model has no implementation
qualification: NOT_QUALIFIED
evidence: [services/asset/, scripts/verify.py, conformance/run.py]
defeating_cases: [CONF-I4-DEF, CONF-I5-DEF, CONF-I7-DEF, CONF-I8-DEF]
```

```yaml
surface: adapters/ollama
operation: invoke_model under a declared Model Binding
artifact_revision: feat/federation-harness-and-hardening (uncommitted tree)
model_and_host: Claude Opus 5, Claude Code CLI, Windows 11
scores:
  reachability: PARTIAL     # bindings and refusals declared; no invocation path executes
  commitment: PARTIAL
  provenance: FULL          # binding, adapter, provider, model, version, runtime, host, projection, boundary, meters recorded
  retraction: NONE          # no model-caused effective change exists to counter
earn_it:
  value: OPEN
  reviewer: unassigned - Bdo
assessment_state: OPEN
minimum_verdict: underivable while earn_it is OPEN
soveraeign_checks:
  same_world_parity: UNATTESTABLE
  typed_authority: PASS
  independent_observation: UNATTESTABLE
  receipt_completeness: UNATTESTABLE    # invocation records are fixtures, not captured runs
  effect_honesty: PASS
  cold_start_competence: UNATTESTABLE
  two_binding_proof: FAIL
  local_sovereignty: PASS
  model_substitutability: PARTIAL       # two bindings declared, neither executed
qualification: NOT_QUALIFIED
evidence: [adapters/ollama/, decisions/0027-local-model-adapter.md]
defeating_cases: [14 fixtures under adapters/ollama/fixtures/]
```

## Leading questions, with recommendations

**Q1 · Through which surface does a ratification become real?**
`OPEN-SEAMS.md` S12 records your own 2026-08-23 input: a code-owner review click
cannot be the ratification surface, and the Console Service is the chartered
home for one — but Console is `CHARTERED_NOT_IMPLEMENTED` behind O18. A chat
instruction is a third surface, and no record can cite it.
*Recommendation:* rule an interim mechanism — a ruling is real when it appears
in a decision record's `Status:` line and the matching `STATUS.yaml` field, in
your words, with CODEOWNERS as transport rather than authority. That is one
decision record, it unblocks every other item here, and it does not pre-empt the
Console surface when that exists.

**Q2 · Does the anchoring evidence get a verifiable local path, or do the
citations get demoted?**
Two options, and they lead different places. (a) Restore
`lineage/evidence/core/` to the local checkout, gitignored, and commit
`lineage/EXTERNAL-SOURCES.lock` carrying digests and clause identifiers only —
citations become verifiable and `PUBLICATION.md` is honored because no content
is published. (b) Rewrite the seven records in group C to cite clause type
rather than file path, and mark the anchoring ground unavailable by design.
*Recommendation:* (a). It is the smaller change, it is what `decisions/0003`
already prescribes, and (b) permanently weakens the founding spine's evidence to
"trust the summary".

**Q3 · Does a judgement-only record need witnessing before ratification?**
`PRD.md` gives one lifecycle, `OPEN -> BUILT -> WITNESSED -> RATIFIED`, and
`SPEC.md`'s Conformance boundary describes it in terms of tests and independent
runs. A boundary or vocabulary record has no implementation to witness, so the
`WITNESSED` step has no content for it.
*Recommendation:* rule that the lifecycle has two paths — executable claims pass
through `WITNESSED`, judgement claims run `OPEN -> PROPOSED -> RATIFIED` — and
write it into `PRD.md`'s Requirement lifecycle. Without it, group A is held at a
step that cannot be performed, which is a rule doing no work.

**Q4 · Will you issue the `earn_it` judgement for the Asset Service proving
operation?**
It is the single input that moves both assessment records above from `OPEN` to
`COMPLETE`, after which every remaining failure is mechanical and a witness can
settle it.
*Recommendation:* issue `SUBSTANTIVE` with yourself as reviewer for the Asset
Service. Removing the model path would remove the capability rather than a
convenience, which is the test the document states.

**Q5 · Ratify group A as a batch now, or hold everything for one pass?**
*Recommendation:* batch now. Those five carry no anchoring dependency and no
built surface, so waiting cannot improve them, and ratifying them shrinks the
remaining spine from twelve records to seven.

**Q6 · Does retraction have to be `FULL` for the Soveraeign bar (S13)?**
Leg 2 of your instruction is that bar, so its internal ambiguity propagates into
every ratification made under it.
*Recommendation:* rule `FULL` within the phase's admitted effect envelope, and
edit the `AI-NATIVE.md` list so "all-`FULL`" is literally true. As written the
document contradicts its own summary of itself.

## What this screen did not do

It ratified nothing, changed no `Status:` line, and altered no `STATUS.yaml`
field. `AGENTS.md` reserves ratification to Bdo and forbids an agent presenting
its synthesis as Bdo's judgement. `SPEC.md`'s Conformance boundary requires an
independent run before `WITNESSED`, and this session dispatched the work in
groups B and C, so it cannot witness that work either.

The reachable next operation, admissible without any ruling above: run `sov-qa`
or `sov-witness` against the working tree to supply the independent observation
group B is missing. It needs no gate, and it converts six `NOT_WITNESSED` fields
into either `WITNESSED` or a recorded dissent.
